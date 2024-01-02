import json
import os
import boto3
import requests
import upsert_data_to_index


def lambda_handler(event, context):
    upsert_data_to_index.main()
