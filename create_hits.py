import boto3
import argparse
import json
import time
import xml.etree.ElementTree as ET


def get_args():
    parser = argparse.ArgumentParser(description='HIT info')

    ## Study description 
    parser.add_argument('--title', type=str)
    parser.add_argument('--description', type=str)
    parser.add_argument('--keywords', type=str)

    ## Study details
    parser.add_argument('--study_url', type=str)
    parser.add_argument('--completion_code', type=str)
    parser.add_argument('--reward', type=str)
    parser.add_argument('--num_parts', type=int)
    parser.add_argument('--parts_per_hit', type=int)
    parser.add_argument('--time', type=int, help="Expected time in minutes")
    parser.add_argument('--max_time', type=int, help = "Max time in minutes")
    parser.add_argument('--auto_approve', type=int, help = "Days until auto-approval")
    

    ## Qualifications for participant exclusion 

    parser.add_argument('--us_location',
                        action='store_true') 

    parser.add_argument('--masters',
                        action='store_true') 

    parser.add_argument('--qualification', type=str, default = '', help="Exclude if assigned this qualification")

    ## Other parameters
    parser.add_argument('--wait', type=int, default = '', help="Time to wait in minutes")
    parser.add_argument('--sandbox',
                        action='store_true') 

    parser.add_argument('--study_name', type =str, default = 'test.txt')

    return parser.parse_args()

def convert_to_seconds(time, unit='minutes'):
    if unit == 'minutes':
        return time*60
    elif unit == 'hours':
        return time*60*60
    elif unit == 'days':
        return time*60*60*24
    else:
        print("Enter valid unit (minutes, hours, days)") 


def make_qualifications(args):
    #documentation: https://docs.aws.amazon.com/AWSMechTurk/latest/AWSMturkAPI/ApiReference_QualificationRequirementDataStructureArticle.html

    qualifications = []

    if args.sandbox:
        masters_qualification = "2ARFPLSP75KLA8M8DH1HTEQVJT3SY6"
    else:
        masters_qualification = "2F1QJWKUDD8XADTFD2Q0G6UTO95ALH"


    if args.masters:
        qualifier = {
            "QualificationTypeId": masters_qualification,  # Masters Qualification
            "Comparator": "Exists"
        }

        qualifications.append(qualifier)

    if args.us_location: 
        qualifier = {
            "QualificationTypeId": "00000000000000000071",  
            "Comparator": "EqualTo",
            "LocaleValues": [{"Country": "US"}],
            "RequiredToPreview": True
        }

        qualifications.append(qualifier)

    if len(args.qualification) > 0:
        qualifier = {
            "QualificationTypeId": args.qualification,
            "Comparator": "DoesNotExist",
            "RequiredToPreview": True
        }

        qualifications.append(qualifier)

    return qualifications




def get_endpoint_url(sandbox):
    if sandbox:
        return "https://mturk-requester-sandbox.us-east-1.amazonaws.com"
    else:
        return "https://mturk-requester.us-east-1.amazonaws.com"

def make_question(url):
    question = f"""<QuestionForm xmlns="http://mechanicalturk.amazonaws.com/AWSMechanicalTurkDataSchemas/2017-11-06/QuestionForm.xsd">
    <Question>
        <QuestionIdentifier>SurveyLink</QuestionIdentifier>
        <DisplayName>Survey</DisplayName>
        <QuestionContent>
            <Text>Copy-paste the following url into a separate browser tab or window</Text>
            <Text>{url}</Text>
            <Text>After completing the survey, enter the provided completion code below.</Text>
        </QuestionContent>
        <AnswerSpecification>
            <FreeTextAnswer>
                <NumberOfLinesSuggestion>1</NumberOfLinesSuggestion>
            </FreeTextAnswer>
        </AnswerSpecification>
    </Question>
    </QuestionForm>
    """
    return question 
        
def create_hit(client, args):
    hit = client.create_hit(
        Title = args.title,
        Description = args.description,
        Keywords = args.keywords,
        Reward = args.reward,
        MaxAssignments = args.parts_per_hit,## to avoid extra fees 
        AssignmentDurationInSeconds = convert_to_seconds(args.time),
        LifetimeInSeconds = convert_to_seconds(args.max_time),
        AutoApprovalDelayInSeconds = convert_to_seconds(args.auto_approve, 'days'),
        Question = make_question(args.study_url),
        QualificationRequirements = make_qualifications(args)
        )

    return hit["HIT"]["HITId"]

def assign_qualification(client, hit_id, qualification):
    assignments = client.list_assignments_for_hit(
            HITId=hit_id, AssignmentStatuses=["Submitted"]
        )["Assignments"]

    ids = []

    for worker in assignments:
        worker_id = worker["WorkerId"]
                
        # Assign past participation qualification
        client.associate_qualification_with_worker(
            QualificationTypeId=qualification,
            WorkerId=worker_id,
            IntegerValue=1,  # Any value works
            SendNotification=False
        )
        ids.append(worker_id)

    return ids



def main():
    args = get_args()

    ## Create mturk session 
    session = boto3.Session(profile_name="mturk-requester")

    client = session.client(
        "mturk",
        region_name="us-east-1",  # MTurk is only in us-east-1
        endpoint_url=get_endpoint_url(args.sandbox)
    )

    # Number of participants always round up to the next parts_per_hit. So if num_parts is between 91 and 98 and parts_per_hit is 9, we will recruit 99 participants. So at most we end up recruiting parts_per_hit-1 extra participants. 
    num_hits = args.num_parts//args.parts_per_hit 
    if args.num_parts % args.parts_per_hit !=0:
        num_hits+=1 #because integer division rounds down

    all_ids = []
    for i in range(num_hits):
        hit_id = create_hit(client, args)
        print(f"Submitted HIT {i+1}. ID: {hit_id}")

        hit_status = client.get_hit(HITId=hit_id)["HIT"]["HITStatus"]

        while hit_status != "Reviewable":
            time.sleep(convert_to_seconds(args.wait))
            hit_status = client.get_hit(HITId=hit_id)["HIT"]["HITStatus"]

        ids = assign_qualification(client, hit_id, args.qualification)

        print("Assigned qualifications")

        all_ids.append({hit_id: ids})

    ids_str = json.dumps(all_ids)

    with open(args.study_name, 'w') as f:
        f.write(ids_str)

main()




