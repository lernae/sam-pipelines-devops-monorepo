import json

def lambda_handler(event, context):
    print(event)
    githubEventPayload=json.loads(event['body'])
    modifiedFiles = githubEventPayload["commits"][0]["modified"]
    print("modified files")
    print(modifiedFiles)
    #full path
    for filePath in modifiedFiles:
        # Extract folder name
        folderName = (filePath[:filePath.find("/")])
        print(folderName)
        break

    #start the pipeline
    if len(folderName)>0:
        print("inside if")
        # Codepipeline name is foldername. 
        # We can read the configuration from S3 as well. 
        if not exists_pipeline(folderName):
            print("pipeline does not exist")
            create_pipeline(folderName)
        returnCode = start_code_pipeline(folderName)

    return {
        'statusCode': 200,
        'body': json.dumps('Modified project in repo:' + folderName)
    }
    

def start_code_pipeline(pipelineName):
    client = codepipeline_client()
    print('starting pipeline ',pipelineName)
    response = client.start_pipeline_execution(name=pipelineName)
    print('start_pipeline_execution response ',response)
    return True

def create_pipeline(pipelineName):
    client = codebuild_client()
    print('creating pipeline')
    response = client.start_build(projectName='create_pipeline',
                                  environmentVariablesOverride=[
                                        {
                                            'name': 'PIPELINE_NAME',
                                            'value': pipelineName,
                                            'type': 'PLAINTEXT'
                                        }
                                    ])
    return True

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
