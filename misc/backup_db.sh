#!/bin/bash
set -ex

DIR=`date +%Y%m%d`
DEST="../db_backups/${DIR}"
mkdir -p "${DEST}"

mongodump --uri ${MONGO_DB_URI} -d barlamane --out "${DEST}"
