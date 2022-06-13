import json
import time


def lambda_handler(event, context):
    print(event)
    githubEventPayload=json.loads(event['body'])
    modifiedFiles = githubEventPayload["commits"][0]["modified"] or githubEventPayload["commits"][0]["added"] or githubEventPayload["commits"][0]["deleted"]
    print("modified files")
    print(modifiedFiles)
    #full path
    for filePath in modifiedFiles:
        # Extract folder name
        folderName = (filePath[:filePath.find("/")])
        print(folderName)
        break

    client = codepipeline_client()
    #start the pipeline
    if len(folderName)>0:
        try:
            response = client.get_pipeline(name=folderName)
            folderFound = response['pipeline']['name']
            print('found? ', folderFound)
            client.start_pipeline_execution(name=folderName) # pipeline runs at first creation so no need to trigger this if creating it first time
        except:
            print('pipeline ', folderName, ' does not exist')
            print('creating pipeline')
            start_codebuild(projectName='create_pipeline',
                            envVarList=[
                                {
                                    'name': 'ENV_PIPELINE_NAME',
                                    'value': folderName,
                                    'type': 'PLAINTEXT'
                                }
                            ])
        return {
            'statusCode': 200,
            'body': json.dumps('Modified project in repo:' + folderName)
        }
    return {
        'statusCode': 200,
        'body': json.dumps('No modified project in repo')
    }


def start_codebuild(projectName, envVarList):
    print('starting codebuild ',projectName)
    client = codebuild_client()
    response = client.start_build(projectName=projectName, environmentVariablesOverride=envVarList)
    print('start_build response ',response)
    # Check for the status of the build
    buildId = response['build']['id']
    print('buildId ',buildId)
    status = check_build_status(buildId)
    return status


def check_build_status(buildId):
    import boto3
    global cbclient
    if not cbclient:
        cbclient = boto3.client('codebuild')
    status = "failed"
    while status != "SUCCEEDED" and status != "FAILED":
        response = cbclient.batch_get_builds(ids=[buildId])
        status = response['builds'][0]['buildStatus']
        print('build status ',status)
        if status == "IN_PROGRESS":
            time.sleep(5)
    return status


cpclient = None
def codepipeline_client():
    import boto3
    global cpclient
    if not cpclient:
        cpclient = boto3.client('codepipeline')
    return cpclient


cbclient = None
def codebuild_client():
    import boto3
    global cbclient
    if not cbclient:
        cbclient = boto3.client('codebuild')
    return cbclient