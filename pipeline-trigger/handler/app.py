import json
import boto3
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

    client = boto3.client('codepipeline')
    # csclient = boto3.client('codestar-connections')
    # csresp = csclient.list_connections(ProviderTypeFilter='GitHub') # doesn't make sense to get this each time, set this once
    #start the pipeline
    if len(folderName)>0:
        try:
            response = client.get_pipeline(name=folderName)
            folderFound = response['pipeline']['name']
            print('found? ', folderFound)
        except:
            print('pipeline ', folderName, ' does not exist')
            cb_client = codebuild_client()
            print('creating pipeline')
            start_codebuild(projectName='create_pipeline',
                                             envVarList=[
                                                  {
                                                      'name': 'ENV_PIPELINE_NAME',
                                                      'value': folderName,
                                                      'type': 'PLAINTEXT'
                                                  },
                                                  {
                                                      'name': 'ENV_RESOURCE_TYPE',
                                                      'value': 'lambda',
                                                      'type': 'PLAINTEXT'
                                                  }
                                             ])
        client.start_pipeline_execution(name=folderName)
        print("finished")
        return {
            'statusCode': 200,
            'body': json.dumps('Modified project in repo:' + folderName)
        }
    print("finished")
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


def start_code_pipeline(pipelineName):
    client = codepipeline_client()
    print('starting pipeline ', pipelineName)
    response = client.start_pipeline_execution(name=pipelineName)
    print('start_pipeline_execution response ', response)
    # return True


def create_pipeline(pipelineName):
    client = codebuild_client()
    print('creating pipeline')
    response = client.start_build(projectName='create_pipeline',
                                  environmentVariablesOverride=[
                                        {
                                            'name': 'ENV_PIPELINE_NAME',
                                            'value': pipelineName,
                                            'type': 'PLAINTEXT'
                                        }
                                    ])
    # return True


def exists_pipeline(pipelineName):
    client = codepipeline_client()
    print('checking if pipeline ', pipelineName, ' exists')
    exists = False
    try:
        response = client.get_pipeline(name=pipelineName)
        print('found ', response.pipeline.name)
        exists = True
    except:
        print('pipeline ', pipelineName, ' does not exist')
    return exists


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