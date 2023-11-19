

def objective(trial, identifier, archive_db_url):

###--- definition coroutines ---###
### We have to keep to coroutines in the objective function,
### otherwise the workers do not know about those until we preinstall those.
    {% macro local_coroutines_include() %}{% include 'nats_coroutines.py' %}{% endmacro %}
    {{ local_coroutines_include()|indent }} # default is indent of 4 spaces!
###--- end coroutines ---###


    logger = logging.getLogger('objective')
    logger.setLevel(logging.DEBUG)


    archive_db_engine = create_engine(archive_db_url)

    logger.warning('entering')

    # Compiling settings for effectuation
    settings = []
    for setting_name, setting_config in config.get('settings').get('sysctl').items():
        constraints = setting_config.get('constraints')
        step_width = setting_config.get('step')
        suggested_value = trial.suggest_int(setting_name, constraints.get('lower') , constraints.get('upper'), step_width)
        if setting_name in ['net.ipv4.tcp_rmem', 'net.ipv4.tcp_wmem']:
            settings.append(f"sudo sysctl -w {setting_name}='4096 131072 {suggested_value}';")
        else:
            settings.append(f"sudo sysctl -w {setting_name}='{suggested_value}';")
    settings = '\n'.join(settings)

    is_setting_explored = False
    setting_id = hashlib.sha256(str.encode(settings_full)).hexdigest()[0:6]

    breeder_table_name = f"from_breeder_name" # TBD global knowledge db table nam
    query = text("SELECT * FROM :table_name WHERE :table_name.setting_id == :setting_id")

    query = query.bindparams(bindparam("table_name", breeder_table_name, type_=String),
                             bindparam("setting_id", setting_id, type_=String))

    archive_db_data = archive_db_engine.execute(query).fetchall()

    if archive_db_data:
        is_setting_explored = True
        rtt = archive_db_data[0].get('setting_result').get('rtt')
        delivery_rate = archive_db_data[0].get('setting_result').get('delivery_rate')

    if not is_setting_explored:
        logger.warning('doing effectuation')
        settings_data = dict(settings=settings)
        asyncio.run(send_msg_via_nats(subject=f'effectuation_{identifier}', data_dict=settings_data))

        logger.warning('gathering recon')
        metric = json.loads(asyncio.run(receive_msg_via_nat(subject=f'recon_{identifier}')))
        metric_value = metric.get('metric')
        rtt = float(metric_value['tcp_rtt'])
        delivery_rate = float(metric_value['tcp_delivery_rate_bytes'])
        logger.warning(f'metric received {metric_value}')

    logger.warning('Done')

    return rtt, delivery_rate


