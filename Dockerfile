FROM hmlandregistry/dev_base_python_flask:3

# ---- Database stuff start
RUN yum install -y -q postgresql-devel

ENV SQL_HOST=postgres \
	SQL_DATABASE=register_db \
	ALEMBIC_SQL_USERNAME=alembic_user \
	SQL_USE_ALEMBIC_USER=no \
	APP_SQL_USERNAME=register_db_user \
  SQL_PASSWORD=password \
  SQLALCHEMY_POOL_SIZE=10 \
  SQLALCHEMY_POOL_RECYCLE="3300"
# ---- Database stuff end

# app-specific stuff here
ENV APP_NAME=register \
  REGISTER_NAME="Local Land Charges" \
  REGISTER_KEY_FIELD=local-land-charge \
  REGISTER_RECORD=/src/config/record.json \
  REGISTER_ROUTEKEY=llc.local-land-charge \
  EXCHANGE_NAME=llc-charge-exchange \
  EXCHANGE_TYPE=topic \
  RABBIT_URL=amqp://guest:guest@rabbitmq:5672// \
  KOMBU_LOG_LEVEL=INFO \
  VALIDATION_BASE_URI=http://validation-api:8080/ \
  VALIDATION_ENDPOINT=validate \
  PUBLIC_KEY="certs/test_public.pem" \
  PUBLIC_PASSPHRASE="thisisapublicpassphrase" \
  MAX_HEALTH_CASCADE=6
# app-specific stuff end

# Get the python environment ready.
# Have this at the end so if the files change, all the other steps don't need to be rerun. Same reason why _test is
# first. This ensures the container always has just what is in the requirements files as it will rerun this in a
# clean image.
ADD requirements_test.txt requirements_test.txt
ADD requirements.txt requirements.txt
RUN pip3 install -r requirements.txt && \
  pip3 install -r requirements_test.txt
