

def objective(trial, identifier, archive_db_url, locking_db_url, breeder_name):

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
    setting_id = hashlib.sha256(str.encode(settings)).hexdigest()[0:6]

    breeder_table_name = f"{breeder_name}"
    query = f"SELECT * FROM {breeder_table_name} WHERE {breeder_table_name}.setting_id = '{setting_id}';"

    archive_db_data = archive_db_engine.execute(query).fetchall()

    if archive_db_data:
        is_setting_explored = True
        rtt = archive_db_data[0].get('setting_result').get('rtt')
        delivery_rate = archive_db_data[0].get('setting_result').get('delivery_rate')

    if not is_setting_explored:
        logger.warning('doing effectuation')
        settings_data = dict(settings=settings)

        # get lock to gate other objective runs
        locker = pals.Locker('network_breeder_effectuation', locking_db_url)

        dlm_lock = locker.lock(target)

        if not dlm_lock.acquire(acquire_timeout=600):
            task_logger.debug("Could not aquire lock for {target}")


        asyncio.run(send_msg_via_nats(subject=f'effectuation_{identifier}', data_dict=settings_data))

        logger.warning('gathering recon')
        metric = json.loads(asyncio.run(receive_msg_via_nats(subject=f'recon_{identifier}')))


        # release lock to let other objective runs effectuation
        dlm_lock.release()

        metric_value = metric.get('metric')
        rtt = float(metric_value['tcp_rtt'])
        delivery_rate = float(metric_value['tcp_delivery_rate_bytes'])
        logger.warning(f'metric received {metric_value}')

    logger.warning('Done')

    return rtt, delivery_rate


