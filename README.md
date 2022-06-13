# CI/CD for mono repo with SAM pipelines [WIP]


## Intro

This repo aims to provide a first implementation of  CI/CD pipelines for mono repo based on 
* Github repo
* Multi Accounts (CI/CD dedicated account, Staging account and Prod account)
* [SAM pipelines](https://aws.amazon.com/blogs/compute/introducing-aws-sam-pipelines-automatically-generate-deployment-pipelines-for-serverless-applications/)
* AWS CodePipeline, CodeBuild etc.
* [Monorepo selective pipeline trigger](https://aws.amazon.com/blogs/devops/integrate-github-monorepo-with-aws-codepipeline-to-run-project-specific-ci-cd-pipelines/)

![mono repo trigger high level](https://d2908q01vomqb2.cloudfront.net/7719a1c782a1ba91c031a682a0a2f8658209adbf/2021/04/23/Codepipeline.jpg)

![mono repo trigger flow](https://d2908q01vomqb2.cloudfront.net/7719a1c782a1ba91c031a682a0a2f8658209adbf/2021/04/23/Codepipeline-Sample-Arch.jpg)

## Components
* devops repo (this repo) contains:
   * pipeline-trigger: the implementation of this [blog post](https://aws.amazon.com/blogs/devops/integrate-github-monorepo-with-aws-codepipeline-to-run-project-specific-ci-cd-pipelines/) to be able to trigger the right pipeline based on what changed
   * pipeline buildspec files and pipeline template
   * sub project common template
* appdev repo (github.com/lernae/sam-pipelines-appdev-monorepo/) contains:
   * `projectX`: the folder containing the code for the SAM app (`src/`)

# Usage

## Prerequisite

* [SAM cli](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html)
* A github account
* one or more AWS Accounts (preferably 3: one hosting the CI/CD pipeline and related resources, one for staging and one for Prod)


1. Fork [this repo](https://github.com/lernae/sam-pipelines-devops-monorepo/) and the [appdev repo](https://github.com/lernae/sam-pipelines-appdev-monorepo/)
   ```
   git clone https://github.com/<YOUR ALIAS>/sam-pipelines-devops-monorepo.git
   cd sam-pipelines-devops-monorepo
   ```
1. Setup your different aws profile for each account. For below steps, we have set up:
* `cicd` profile to the account hosting the pipeline, pipeline trigger, sub project templates
* `staging` profile for the first stage of deployment 
* `prod` profile for the second stage of deployment

## Setup Mono repo pipeline trigger (deployed in ci/cd account) 
1. Create a CodeStarConnection for connecting to the GitHub repo's.
```shell
aws codestar-connections create-connection --provider-type GitHub --connection-name GitRepositoryConnection --profile cicd
# Go to aws console -> CodePipeline -> Settings -> [Connections](https://us-east-1.console.aws.amazon.com/codesuite/settings/connections) -> select this newly created connection with name "GitRepositoryConnection" and then pick "Update pending connection" on top right.
# Click on "Install a new app" -> pick the github namespace -> Configure and follow prompts for "Repository access".  
# Select both appdev and devops repositories under "Only select repositories" under "Repository access" then hit "save".  Then you will be redirected back to the "Connect to Github" window.  Here click on "Connect"
# Ensure the recently created connection now has status set to "Available"
```
Click on the connection and copy its ARN.  Go to template.yaml inside the pipeline-trigger folder in the devops repo.  Update below line with your ARN for the connection in "Parameters" section:
```
 CodeStarConnectionArn:
    Type: String
    Default: "arn:aws:codestar-connections:<your-cicd-region>:<your-cicd-account>:connection/your-connection" 
```
2. Deploy the pipeline trigger.  First, remove s3_bucket and parameter_overrides from samconfig.toml under pipeline-trigger folder.  These will get added after you run the next command.
Then run below, accept defaults (hit enter) except for "PipelineTriggerFunction may not have authorization defined, Is this okay? [y/N]: y" where you enter 'y'
   ```
   cd pipeline-trigger
   sam deploy --guided --profile cicd
   ```
Going through the prompts, will look as the following:
```shell

$ sam deploy --guided --profile cicd

Configuring SAM deploy
======================

        Looking for config file [samconfig.toml] :  Found
        Reading default arguments  :  Success

        Setting default arguments for 'sam deploy'
        =========================================
        Stack Name [pipeline-trigger]:
        AWS Region [us-east-1]:
        Parameter PipelineName []:
        Parameter CodeStarConnectionArn [arn:aws:codestar-connections:us-east-1:<your-cicd-acct>:connection/<conn-id>]:
        #Shows you resources changes to be deployed and require a 'Y' to initiate deploy
        Confirm changes before deploy [Y/n]:
        #SAM needs permission to be able to create roles to connect to the resources in your template
        Allow SAM CLI IAM role creation [Y/n]:
        #Preserves the state of previously provisioned resources when an operation fails
        Disable rollback [y/N]:
        PipelineTriggerFunction may not have authorization defined, Is this okay? [y/N]: y
        Save arguments to configuration file [Y/n]:
        SAM configuration file [samconfig.toml]:
        SAM configuration environment [default]:

```
This creates a CloudFormation stack in your ci/cd account named 'pipeline-trigger' and it will not deploy until you confirm you want to deploy the changes as per next step.
Next, enter 'y' when asked to "Deploy this changeset?" as below
```shell
CloudFormation stack changeset
---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
Operation                                                                     LogicalResourceId                                                             ResourceType                                                                  Replacement
---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
+ Add                                                                         CodeBuildServiceRole                                                          AWS::IAM::Role                                                                N/A
+ Add                                                                         PipelineTriggerCreatePipelineTask                                             AWS::CodeBuild::Project                                                       N/A
+ Add                                                                         PipelineTriggerFunctionPipelineTriggerPermissionProd                          AWS::Lambda::Permission                                                       N/A
+ Add                                                                         PipelineTriggerFunctionRole                                                   AWS::IAM::Role                                                                N/A
+ Add                                                                         PipelineTriggerFunction                                                       AWS::Lambda::Function                                                         N/A
+ Add                                                                         ServerlessRestApiDeployment565c0f068a                                         AWS::ApiGateway::Deployment                                                   N/A
+ Add                                                                         ServerlessRestApiProdStage                                                    AWS::ApiGateway::Stage                                                        N/A
+ Add                                                                         ServerlessRestApi                                                             AWS::ApiGateway::RestApi                                                      N/A
---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Changeset created successfully. arn:aws:cloudformation:us-east-1:586770803976:changeSet/samcli-deploy1655130726/1190ea5d-5d26-474e-a207-6cc43f3fe095


Previewing CloudFormation changeset before deployment
======================================================
Deploy this changeset? [y/N]:y
```
Upon successful deployment of the pipeline trigger, you will see:
```shell
CloudFormation outputs from deployed stack
---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
Outputs
---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
Key                 PipelineTriggerApi
Description         API Gateway endpoint URL for Prod stage for Pipeline Trigger function
Value               https://abcd123.execute-api.<region>.amazonaws.com/Prod/
---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Successfully created/updated stack - pipeline-trigger in us-east-1
```
3. Add webhook to your appdev github repo using the API GW endpoint URL from prev step's outputs (see "Creating a GitHub webhook" [this blog](https://aws.amazon.com/blogs/devops/integrate-github-monorepo-with-aws-codepipeline-to-run-project-specific-ci-cd-pipelines/) for more details making sure you selected `Content type` as `application/json` !!!)

## Bootstrap

1. Bootstrap your accounts
   1. create a dummy user into CI/CD account (to work around https://github.com/aws/aws-sam-cli/issues/3857)
      ```bash
      aws iam create-user --user-name "dummy-aws-sam-cli-user" --profile cicd
      ```
   1. Bootstrap cicd accounts.  Ensure you are inside the root directory in the devops repo shadow. If inside pipeline-trigger folder, `cd .. ` first.
      ```bash
      sam pipeline init --bootstrap
      ```
      ```
      sam pipeline init generates a pipeline configuration file that your CI/CD system
      can use to deploy serverless applications using AWS SAM.
      We will guide you through the process to bootstrap resources for each stage,
      then walk through the details necessary for creating the pipeline config file.

      Please ensure you are in the root folder of your SAM application before you begin.

      Select a pipeline template to get started:
            1 - AWS Quick Start Pipeline Templates
            2 - Custom Pipeline Template Location
      Choice: 1

      Cloning from https://github.com/aws/aws-sam-cli-pipeline-init-templates.git (process may take a moment)
      Select CI/CD system
            1 - Jenkins
            2 - GitLab CI/CD
            3 - GitHub Actions
            4 - Bitbucket Pipelines
            5 - AWS CodePipeline
      Choice: 5
      You are using the 2-stage pipeline template.
      _________    _________ 
      |         |  |         |
      | Stage 1 |->| Stage 2 |
      |_________|  |_________|

      Checking for existing stages...

      [!] None detected in this account.

      Do you want to go through stage setup process now? If you choose no, you can still reference other bootstrapped resources. [y/N]: y

      For each stage, we will ask for [1] stage definition, [2] account details, and [3]
      reference application build resources in order to bootstrap these pipeline
      resources.

      We recommend using an individual AWS account profiles for each stage in your
      pipeline. You can set these profiles up using aws configure or ~/.aws/credentials. See
      [https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-getting-started-set-up-credentials.html].


      Stage 1 Setup

      [1] Stage definition
      Enter a configuration name for this stage. This will be referenced later when you use the sam pipeline init command:
      Stage configuration name: test

      [2] Account details
      The following AWS credential sources are available to use.
      To know more about configuration AWS credentials, visit the link below:
      https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html                
            1 - Environment variables (not available)
            2 - default (named profile)
            3 - dev (named profile)
            4 - test (named profile)
            5 - prod (named profile)
            6 - cicd (named profile)
            q - Quit and configure AWS credentials
      Select a credential source to associate with this stage: 4
      Associated account <TEST ACCOUNT ID> with configuration test.

      Enter the region in which you want these resources to be created [us-east-1]: 
      Enter the pipeline IAM user ARN if you have previously created one, or we will create one for you []: arn:aws:iam::<CICD ACCOUNT ID>:user/dummy-aws-sam-cli-user

      [3] Reference application build resources
      Enter the pipeline execution role ARN if you have previously created one, or we will create one for you []: 
      Enter the CloudFormation execution role ARN if you have previously created one, or we will create one for you []: 
      Please enter the artifact bucket ARN for your Lambda function. If you do not have a bucket, we will create one for you []: 
      Does your application contain any IMAGE type Lambda functions? [y/N]: 

      [4] Summary
      Below is the summary of the answers:
            1 - Account: <TEST ACCOUNT ID>
            2 - Stage configuration name: test
            3 - Region: us-east-1
            4 - Pipeline user ARN: arn:aws:iam::<CICD ACCOUNT ID>:user/dummy-aws-sam-cli-user
            5 - Pipeline execution role: [to be created]
            6 - CloudFormation execution role: [to be created]
            7 - Artifacts bucket: [to be created]
            8 - ECR image repository: [skipped]
      Press enter to confirm the values above, or select an item to edit the value: 

      This will create the following required resources for the 'test' configuration: 
            - Pipeline execution role
            - CloudFormation execution role
            - Artifact bucket
      Should we proceed with the creation? [y/N]: y
      The following resources were created in your account:
            - Pipeline execution role
            - CloudFormation execution role
            - Artifact bucket
      View the definition in .aws-sam/pipeline/pipelineconfig.toml,
      run sam pipeline bootstrap to generate another set of resources, or proceed to
      sam pipeline init to create your pipeline configuration file.

      Checking for existing stages...

      Only 1 stage(s) were detected, fewer than what the template requires: 2.

      Do you want to go through stage setup process now? If you choose no, you can still reference other bootstrapped resources. [y/N]: y

      For each stage, we will ask for [1] stage definition, [2] account details, and [3]
      reference application build resources in order to bootstrap these pipeline
      resources.

      We recommend using an individual AWS account profiles for each stage in your
      pipeline. You can set these profiles up using aws configure or ~/.aws/credentials. See
      [https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-getting-started-set-up-credentials.html].


      Stage 2 Setup

      [1] Stage definition
      Enter a configuration name for this stage. This will be referenced later when you use the sam pipeline init command:
      Stage configuration name: prod

      [2] Account details
      The following AWS credential sources are available to use.
      To know more about configuration AWS credentials, visit the link below:
      https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html                
            1 - Environment variables (not available)
            2 - default (named profile)
            3 - dev (named profile)
            4 - test (named profile)
            5 - prod (named profile)
            6 - cicd (named profile)
            q - Quit and configure AWS credentials
      Select a credential source to associate with this stage: 5
      Associated account <PROD ACCOUNT ID> with configuration prod.


      Enter the region in which you want these resources to be created [us-east-1]: 
      Pipeline IAM user ARN: arn:aws:iam::<CICD ACCOUNT ID>:user/dummy-aws-sam-cli-user

      [3] Reference application build resources
      Enter the pipeline execution role ARN if you have previously created one, or we will create one for you []: 
      Enter the CloudFormation execution role ARN if you have previously created one, or we will create one for you []: 
      Please enter the artifact bucket ARN for your Lambda function. If you do not have a bucket, we will create one for you []: 
      Does your application contain any IMAGE type Lambda functions? [y/N]: 

      [4] Summary
      Below is the summary of the answers:
            1 - Account: <PROD ACCOUNT ID>
            2 - Stage configuration name: prod
            3 - Region: us-east-1
            4 - Pipeline user ARN: arn:aws:iam::<CICD ACCOUNT ID>:user/dummy-aws-sam-cli-user
            5 - Pipeline execution role: [to be created]
            6 - CloudFormation execution role: [to be created]
            7 - Artifacts bucket: [to be created]
            8 - ECR image repository: [skipped]
      Press enter to confirm the values above, or select an item to edit the value: 

      This will create the following required resources for the 'prod' configuration: 
            - Pipeline execution role
            - CloudFormation execution role
            - Artifact bucket
      Should we proceed with the creation? [y/N]: y
      The following resources were created in your account:
            - Pipeline execution role
            - CloudFormation execution role
            - Artifact bucket
      View the definition in .aws-sam/pipeline/pipelineconfig.toml,
      run sam pipeline bootstrap to generate another set of resources, or proceed to
      sam pipeline init to create your pipeline configuration file.

      Checking for existing stages...

      What is the Git provider?
            1 - Bitbucket
            2 - CodeCommit
            3 - GitHub
            4 - GitHubEnterpriseServer
      Choice []: 3
      What is the full repository id (Example: some-user/my-repo)?: <YOUR_GITHUB_ALIAS>/sam-pipelines-appdev-monorepo
      What is the Git branch used for production deployments? [main]: 
      What is the template file path? [template.yaml]:
      We use the stage configuration name to automatically retrieve the bootstrapped resources created when you ran `sam pipeline bootstrap`.

      Here are the stage configuration names detected in .aws-sam/pipeline/pipelineconfig.toml:
            1 - test
            2 - prod
      Select an index or enter the stage 1's configuration name (as provided during the bootstrapping): 1
      What is the sam application stack name for stage 1? [sam-app]: 
      Stage 1 configured successfully, configuring stage 2.

      Here are the stage configuration names detected in .aws-sam/pipeline/pipelineconfig.toml:
            1 - test
            2 - prod
      Select an index or enter the stage 2's configuration name (as provided during the bootstrapping): 2
      What is the sam application stack name for stage 2? [sam-app]: 
      Stage 2 configured successfully.

      To deploy this template and connect to the main git branch, run this against the leading account:
      `sam deploy -t codepipeline.yaml --stack-name <stack-name> --capabilities=CAPABILITY_IAM`.
      SUMMARY
      We will generate a pipeline config file based on the following information:
            What is the Git provider?: GitHub
            What is the full repository id (Example: some-user/my-repo)?: lernae/sam-pipelines-appdev-monorepo
            What is the Git branch used for production deployments?: main
            What is the template file path?: lambda_template.yaml
            Select an index or enter the stage 1's configuration name (as provided during the bootstrapping): 1
            What is the sam application stack name for stage 1?: sam-app
            What is the pipeline execution role ARN for stage 1?: arn:aws:iam::<TEST ACCOUNT ID>:role/aws-sam-cli-managed-test-pip-PipelineExecutionRole-1DLBUQ6UNNQX7
            What is the CloudFormation execution role ARN for stage 1?: arn:aws:iam::<TEST ACCOUNT ID>:role/aws-sam-cli-managed-test-CloudFormationExecutionR-1BGDI9HEH35O
            What is the S3 bucket name for artifacts for stage 1?: aws-sam-cli-managed-test-pipeline-artifactsbucket-au1hjr2128bw
            What is the ECR repository URI for stage 1?: 
            What is the AWS region for stage 1?: us-east-1
            Select an index or enter the stage 2's configuration name (as provided during the bootstrapping): 2
            What is the sam application stack name for stage 2?: sam-app
            What is the pipeline execution role ARN for stage 2?: arn:aws:iam::<PROD ACCOUNT ID>:role/aws-sam-cli-managed-prod-pip-PipelineExecutionRole-125II9ETGPTND
            What is the CloudFormation execution role ARN for stage 2?: arn:aws:iam::<PROD ACCOUNT ID>:role/aws-sam-cli-managed-prod-CloudFormationExecutionR-1X9T0LS7UEXZO
            What is the S3 bucket name for artifacts for stage 2?: aws-sam-cli-managed-prod-pipeline-artifactsbucket-204szu1b7wru
            What is the ECR repository URI for stage 2?: 
            What is the AWS region for stage 2?: us-east-1

      Successfully created the pipeline configuration file(s):
            - codepipeline.yaml
            - assume-role.sh
            - pipeline/buildspec_unit_test.yml
            - pipeline/buildspec_build_package.yml
            - pipeline/buildspec_integration_test.yml
            - pipeline/buildspec_feature.yml
            - pipeline/buildspec_deploy.yml
      ```
      Here it's going to be important to properly use the value shown above:
      * Question 1: ***1 - AWS Quick Start Pipeline Templates***
      * Question 2: ***5 - AWS CodePipeline***
      * Question 3: Stage configuration name: ***test***
      * Question 4:  Account details: ***test (named profile)***
      * Question 5: region ***UP TO YOU***
      * Question 6: Enter the pipeline IAM user ARN if you have previously created one, or we will create one for you []: ***THE ARN OF THE DUMMY USER CREATED PREVIOUSLY !!!!!!***
      * ... Same for Stage 2 with prod as name and prod named profile
2. If on Windows, also run `dos2unix.exe assume-role.sh` to ensure assume-role.sh is in unix format as this shell script is used in CodeBuild builds (that we chose to run on Linux).
```shell
$ dos2unix.exe assume-role.sh
dos2unix: converting file assume-role.sh to Unix format...
```
3. Update your pipeline for Mono repo support.  For reference, check codepipeline.yaml.bkp file. Update `codepipeline.yaml`
    * Under Parameters, add below params.  One is for the type of resource in the appdev repo and subfoldername is what we will use to name the pipeline. 
      ```shell
      ResourceType:
        Type: String
        Description: The type of the resource
        Default: "lambda"
      SubFolderName:
        Type: String
        Description: The sub project folder name
        Default: ""
      ```
    * Replace FullRepositoryId as below (one for app and one for devops repo):
      ```shell
      AppFullRepositoryId:
        Type: String
        Default: "<YOUR_ALIAS>/sam-pipelines-appdev-monorepo"
      DevOpsFullRepositoryId:
        Type: String
        Default: "<YOUR_ALIAS>/sam-pipelines-devops-monorepo"
      ```
    * Add the name for the pipeline to be set to the subfolder name under Properties for the Pipeline:
      ```shell
      Pipeline:
        Type: AWS::CodePipeline::Pipeline
        Properties:
       Name: !Ref SubFolderName
      ```
    * Replace 'Actions' inside Source Stage with below:
    ```shell
          - Name: SourceCodeRepoApp
            ActionTypeId:
              Category: Source
              Owner: AWS
              Provider: CodeStarSourceConnection
              Version: "1"
            Configuration:
              ConnectionArn: !If [CreateConnection, !Ref CodeStarConnection, !Ref CodeStarConnectionArn]
              FullRepositoryId: !Ref AppFullRepositoryId
              BranchName: !If [IsFeatureBranchPipeline, !Ref FeatureGitBranch, !Ref MainGitBranch]
              DetectChanges: false
            OutputArtifacts:
              - Name: SourceCodeAsZipApp
            RunOrder: 1
          - Name: SourceCodeRepoDevOps
            ActionTypeId:
              Category: Source
              Owner: AWS
              Provider: CodeStarSourceConnection
              Version: "1"
            Configuration:
              ConnectionArn: !If [CreateConnection, !Ref CodeStarConnection, !Ref CodeStarConnectionArn]
              FullRepositoryId: !Ref DevOpsFullRepositoryId
              BranchName: !If [IsFeatureBranchPipeline, !Ref FeatureGitBranch, !Ref MainGitBranch]
              DetectChanges: false
            OutputArtifacts:
              - Name: SourceCodeAsZipDevOps
            RunOrder: 1
    ```
    * Comment out "UpdatePipeline" and "ExecuteChangeSet" stages
    * Replace below inside BuildAndPackage stage:
    ```shell
          InputArtifacts:
            - Name: SourceCodeAsZip
          OutputArtifacts:
            - Name: BuildArtifactAsZip
    ```
    * with:
    ```shell
      PrimarySource: SourceCodeAsZipDevOps
    InputArtifacts:
      - Name: SourceCodeAsZipApp
      - Name: SourceCodeAsZipDevOps
    OutputArtifacts:
      - Name: BuildArtifactAsZip
    ```
    * Update DeployTest stage to include the following (InputArtifacts, PrimarySource, SubFolderName) and repeat this step for DeployProd stage:
    ```shell
                   ProjectName: !Ref CodeBuildProjectDeploy
                   PrimarySource: SourceCodeAsZipDevOps
                   EnvironmentVariables: !Sub |
                     [
                       {"name": "ENV_TEMPLATE", "value": "packaged-test.yaml"},
                       {"name": "ENV_REGION", "value": "${TestingRegion}"},
                       {"name": "ENV_STACK_NAME", "value": "${TestingStackName}"},
                       {"name": "ENV_PIPELINE_EXECUTION_ROLE", "value": "${TestingPipelineExecutionRole}"},
                       {"name": "ENV_CLOUDFORMATION_EXECUTION_ROLE", "value": "${TestingCloudFormationExecutionRole}"},
                       {"name": "ENV_BUCKET", "value": "${TestingArtifactBucket}"},
                       {"name": "ENV_SUB_FOLDER_NAME", "value": "${SubFolderName}"},
                       {"name": "ENV_IMAGE_REPOSITORY", "value": "${TestingImageRepository}"}
                     ]
                 InputArtifacts:
                   - Name: BuildArtifactAsZip
                   - Name: SourceCodeAsZipDevOps
    ```
    * Update "CodeBuildProjectBuildAndDeployFeature" and "CodeBuildProjectBuildAndPackage" EnvironmentVariables to include:
    ```shell
           - Name: SUB_FOLDER_NAME
             Value: !Ref SubFolderName
    ```
    * Update buildspec files.  You can check the diff using `diff -r pipeline.bkp pipeline`
    ```shell
     cp -r pipeline.bkp/* pipeline/
    ```
    * After this step, feel free to remove pipeline.bkp folder and its contents as they are the same as pipeline folder now.
1. Commit and push to git for the devops repo changes
    ```
    git add .
    git commit -m "Update pipeline template and buildspec files
    git push
    ```
1. To deploy the pipeline for a subproject, git add, delete or update inside the subproject folder in the appdev repo
    ```
    git commit -a -m "update subproject file"
    git push
    ```
1. This will first create the pipeline, if one doesn't exist already for this subproject.  After that the pipeline will get triggered.
1. If a pipeline already exists, then this will trigger the pipeline for this subproject.

## Setup new subproject
Add the subproject into the appdev repo.  git commit any changes and git push.

## Cleanup a pipeline during POC of this sample
$ sam delete --stack-name <name_of_pipeline_CFN_stack>  --profile cicd

# Credit
This repo is based off of the original sam pipelines monorepo https://github.com/flochaz/sam-pipelines-monorepo with modifications to adapt it to a 2 separate repo approach (one for app code and one for infra related resources)
