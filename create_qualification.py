import boto3

USE_SANDBOX = False

endpoint_url = "https://mturk-requester-sandbox.us-east-1.amazonaws.com" if USE_SANDBOX else "https://mturk-requester.us-east-1.amazonaws.com"


session = boto3.Session(profile_name="mturk-requester")

mturk = session.client(
    "mturk",
    region_name="us-east-1",  # MTurk is only in us-east-1
    endpoint_url=endpoint_url
)

qualification_response = mturk.create_qualification_type(
    Name="spr-adaptation-replication",
    Description="Prevents workers from completing multiple HITs in this study",
    QualificationTypeStatus="Active"
)

qualification_id = qualification_response["QualificationType"]["QualificationTypeId"]
print(f"Created Qualification: {qualification_id}")