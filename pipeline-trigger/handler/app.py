import json
import boto3

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

    client = boto3.client('codepipeline')
    #start the pipeline
    if len(folderName)>0:
        try:
            response = client.get_pipeline(name=folderName)
            if response.pipeline.name == folderName:
                print('found? ', response.pipeline.name)
        except:
            print('pipeline ', folderName, ' does not exist')
            cb_client = codebuild_client()
            print('creating pipeline')
            response = cb_client.start_build(projectName='create_pipeline',
                                             environmentVariablesOverride=[
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

# how to ensure lambda logs if using these?
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