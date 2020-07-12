
from airflow import DAG
from airflow.operators.BashOperator import BashOperator
from airflow.contrib.operators.ssh_operator import SSHOperator
from airflow.contrib.hooks.ssh_hook import SSHHook
from airflow.models import Variable
from airflow.utils.dates import days_ago

DEFAULTS = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': days_ago(2),
    'retries': 0,
    'trigger_rule': 'all_success'
    # 'email': ['airflow@example.com'],
    # 'email_on_failure': False,
    # 'email_on_retry': False,
    # 'queue': 'bash_queue',
    # 'pool': 'backfill',
    # 'priority_weight': 10,
    # 'end_date': datetime(2016, 1, 1),
    # 'wait_for_downstream': False,
    # 'dag': dag,
    # 'sla': timedelta(hours=2),
    # 'execution_timeout': timedelta(seconds=300),
    # 'on_failure_callback': some_function,
    # 'on_success_callback': some_other_function,
    # 'on_retry_callback': another_function,
    # 'sla_miss_callback': yet_another_function,
    }

net_stack_dag = DAG(
        'lnx_net_stack',
        default_args=DEFAULTS,
        description='control loop geared to optimizing \
                    linux network stack dynamics'
)

# perform reconnaisance at target instance
recon_step = BashOperator(
    task_id='reconnaisance',
    bash_command='echo noop',
    dag=net_stack_dag,
)

# perform optimiziation run
optimizing_step = BashOperator(
    task_id='optimize',
    bash_command='echo noop',
    dag=net_stack_dag,
)

# perform config effectuation at target instance
conn_hook = SSHHook(
        remote_host=Variable.get("target"),
        username='root',
        key_file="/opt/airflow/credentials/id_rsa",
        timeout=30,
        keepalive_interval=10
        )

effectuation_step = SSHOperator(
    ssh_hook=conn_hook,
    task_id='effectuation',
    timeout=30,
    command="""
            sysctl -w net.ipv4.tcp_mem="188760 251683	377520";
            sysctl -w net.ipv4.tcp_rmem="4096	131072	6291456";
            sysctl -w net.ipv4.tcp_wmem="4096	131072	6291456";
            sysctl -w net.core.netdev_budget=300;
            sysctl -w net.core.netdev_max_backlog=1000;
            """,
    dag=net_stack_dag,
)

recon_step >> optimizing_step >> effectuation_step
