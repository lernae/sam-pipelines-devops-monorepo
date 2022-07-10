import json
import time


def lambda_handler(event, context):
    print(event)
    githubEventPayload=json.loads(event['body'])
    modifiedFiles = githubEventPayload["commits"][0]["modified"] or githubEventPayload["commits"][0]["added"] or githubEventPayload["commits"][0]["deleted"]
    print("modified files")
    print(modifiedFiles)
    # All folders containing modified files in this commit
    folders = set(map(lambda s: (s[:s.find("/")]), modifiedFiles))
    print(folders)

    if len(folders) > 0:
        client = codepipeline_client()
        #start the pipeline
        resp = client.list_pipelines()
        print(rest)
        pipelines = resp['pipelines']
        print(pipelines)
        pipelineNames = [p['name'] for p in pipelines]

        pipelinesToCreate = list(set(folders) - set(pipelineNames))
        print(pipelinesToCreate)
        pipelinesToStart = list(set(folders) - set(pipelinesToCreate))
        print(pipelinesToStart)
        for folderName in pipelinesToStart:
            print('starting pipeline for ', folderName)
            client.start_pipeline_execution(name=folderName)
            print('started pipeline for ', folderName)

        cbclient = codebuild_client()
        projectName='create_pipeline'
        for folderName in pipelinesToCreate:
            print('pipeline ', folderName, ' does not exist')
            print('creating pipeline')
            cbclient.start_build(projectName=projectName,
                                 environmentVariablesOverride=[{
                                        'name': 'ENV_PIPELINE_NAME',
                                        'value': folderName,
                                        'type': 'PLAINTEXT'
                                }])
            # start_codebuild(projectName='create_pipeline',
            #                 envVarList=[
            #                     {
            #                         'name': 'ENV_PIPELINE_NAME',
            #                         'value': folderName,
            #                         'type': 'PLAINTEXT'
            #                     }
            #                 ])

        return {
            'statusCode': 200,
            'body': json.dumps('Modified project in repo:' + folders)
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