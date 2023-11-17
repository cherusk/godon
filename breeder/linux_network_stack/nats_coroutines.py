
{% raw %}
async def send_msg_via_nats(subject=None, data_dict=None):
    import time
    import nats
    import sys
    # Connect to NATS Server.
    nc = await nats.connect(NATS_SERVER_URL)
    transmit_data = bytes(json.dumps(data_dict), encoding='utf8')
    while True:
        try:
            response = await nc.request(f'{subject}', transmit_data)
            print('Response:', response )
            break
        except nats.errors.NoRespondersError:
            time.sleep(2)
            continue
        except:
            logger.warning('unexpted exception')
            logger.warning(sys.exc_info()[0])
            raise
    await nc.flush()
    await nc.close()
{% endraw %}

async def receive_msg_via_nats(subject=None, timeout=300):
    import nats
    import time
    import sys
    # Connect to NATS Server.
    nc = await nats.connect(NATS_SERVER_URL)
    sub = await nc.subscribe(f'{subject}')
    msg = await sub.next_msg(timeout=timeout)
    print(msg)
    await msg.respond(b'OK')
    await nc.close()
    return msg.data.decode()
