import json
import time


def lambda_handler(event, context):
    print(event)
    githubEventPayload=json.loads(event['body'])
    modifiedFiles = githubEventPayload["commits"][0]["modified"] + githubEventPayload["commits"][0]["added"] + githubEventPayload["commits"][0]["deleted"]
    print("modified files")
    print(modifiedFiles)
    # All folders containing modified files in this commit
    folders = set(map(lambda s: (s[:s.find("/")]), modifiedFiles))
    print(folders)

    if len(folders) > 0:
        client = codepipeline_client()
        resp = client.list_pipelines()
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

        return {
            'statusCode': 200,
            'body': json.dumps('Modified project in repo:')
        }
    return {
        'statusCode': 200,
        'body': json.dumps('No modified project in repo')
    }


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
