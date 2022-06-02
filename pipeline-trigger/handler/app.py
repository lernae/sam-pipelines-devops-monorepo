import json

def lambda_handler(event, context):
    print(event)
    githubEventPayload=json.loads(event['body'])
    modifiedFiles = githubEventPayload["commits"][0]["modified"]
    #full path
    for filePath in modifiedFiles:
        # Extract folder name
        folderName = (filePath[:filePath.find("/")])
        break

    #start the pipeline
    if len(folderName)>0:
        # Codepipeline name is foldername. 
        # We can read the configuration from S3 as well. 
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

cpclient = None
def codepipeline_client():
    import boto3
    global cpclient
    if not cpclient:
        cpclient = boto3.client('codepipeline')
    return cpclient