#!/usr/bin/env python

from src.mq_service import MQService
import json
RABBITMQ_DOCKER_REF = 'rabbitmq'
USER_MGT_QUEUE_NAME = 'user_management'
EMAIL_RESET_PASSWORD = 'EmailResetPassword'
APPNAME = "AiquUserMgt"
# RABBITMQ_DOCKER_REF is docker internal endpoint reference
mq_service = MQService(RABBITMQ_DOCKER_REF, USER_MGT_QUEUE_NAME)
mq_service.create_connection()
db_service = aiqudb(appName = APPNAME)

# message example
# {
#   "action": "EmailResetPassword",
#   "user_info":{
#     "userid":"1",
#     "realmid":"1",
#     "email":"x@x.com"
#   }
# }
def callback(ch, method, properties, body):
	try:
		user_mgt_json = json.loads(body)
		action = user_mgt_json["action"]
		if action == EMAIL_RESET_PASSWORD:
			user_info = user_mgt_json["user_info"]
			user = {
				"userid": user_info["userid"],
				"realmid": user_info["realmid"],
				"email": user_info["email"]
			}
			db_service.send_reset_email(user)
		ch.basic_ack(delivery_tag = method.delivery_tag)
	except Exception as e:
		db_service.log.error(str(e))


if __name__ == '__main__':
    try:
        mq_service.channel.basic_consume(queue=USER_MGT_QUEUE_NAME, on_message_callback=callback)
        mq_service.channel.start_consuming()
    except Exception as e:
        db_service.log.error(str(e))