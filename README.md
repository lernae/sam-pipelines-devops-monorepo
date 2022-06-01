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

#TODO Add Multi account structure diagram with CI/CD account, staging and prod

## Components

* `pipeline-trigger`: the implementation of this [blog post](https://aws.amazon.com/blogs/devops/integrate-github-monorepo-with-aws-codepipeline-to-run-project-specific-ci-cd-pipelines/) to be able to trigger the right pipeline based on what changed
<!-- * `common-pipeline` an example on how you can potentially share the same pipeline config accross project -->
* `projectX`: the sub project folder containing the SAM app to deploy including it's pipeline (`codepipeline.yaml`, `pipeline/`, `.aws-sam/pipelineconfig.toml`), it's business logic code (`hello_world/`) and it's dependent infrastructure (`template.yaml`)




# Usage

## Prerequisite

* [SAM cli](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html)
* A github account
* one or more AWS Accounts (preferably 3: one for CI/CD pipeline hosting, one for staging/QA and one for Prod)


1. Fork repo: https://github.com/flochaz/sam-pipelines-monorepo/fork
   ```
   git clone https://github.com/<YOUR ALIAS>/sam-pipelines-monorepo.git
   cd sam-pipelines-monorepo
   ```
1. Setup your different aws profile for each account. In this instruction
* `dev` profile will point to `dev` account, 
* `cicd` profile to the account hosting the pipeline trigger and all the sub project pipeline
* `staging` profile for the first stage of deployment of the projects pipelines
* `prod` profile for the second stage of deployment



## Setup Mono repo pipeline trigger (deployed in ci/cd account) 

1. Deploy the pipeline trigger
   ```
   cd pipeline-trigger
   sam deploy --guided --profile cicd
   ```
1. Add webhook to your github repo (see "Creating a GitHub webhook" [this blog](https://aws.amazon.com/blogs/devops/integrate-github-monorepo-with-aws-codepipeline-to-run-project-specific-ci-cd-pipelines/) for more details making sure you selected `Content type` as `application/json` !!!)

## Use projectA example

1. (optional) Deploy projectA to your dev account. This will deploy your workload infrastructure
   ```
   cd projectA
   sam deploy --guided --profile dev
   ```
1. Bootstrap your accounts
   1. create a dummy user into CI/CD account (to work around https://github.com/aws/aws-sam-cli/issues/3857)
      ```bash
      aws iam create-user --user-name "dummy-aws-sam-cli-user" --profile cicd
      ```
   1. Bootstrap cicd accounts
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

      Enter the region in which you want these resources to be created [eu-west-3]: 
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
            3 - Region: eu-west-3
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


      Enter the region in which you want these resources to be created [eu-west-3]: 
      Pipeline IAM user ARN: arn:aws:iam::<TEST ACCOUNT ID>:user/aws-sam-cli-managed-test-pipeline-res-PipelineUser-1K08W3GS4AA5Z

      [3] Reference application build resources
      Enter the pipeline execution role ARN if you have previously created one, or we will create one for you []: 
      Enter the CloudFormation execution role ARN if you have previously created one, or we will create one for you []: 
      Please enter the artifact bucket ARN for your Lambda function. If you do not have a bucket, we will create one for you []: 
      Does your application contain any IMAGE type Lambda functions? [y/N]: 

      [4] Summary
      Below is the summary of the answers:
            1 - Account: <PROD ACCOUNT ID>
            2 - Stage configuration name: prod
            3 - Region: eu-west-3
            4 - Pipeline user ARN: arn:aws:iam::<TEST ACCOUNT ID>:user/aws-sam-cli-managed-test-pipeline-res-PipelineUser-1K08W3GS4AA5Z
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
      What is the full repository id (Example: some-user/my-repo)?: flochaz/sam-pipelines-monorepo
      What is the Git branch used for production deployments? [main]: 
      What is the template file path? [template.yaml]: template.yaml
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
            What is the full repository id (Example: some-user/my-repo)?: flochaz/sam-pipelines-monorepo
            What is the Git branch used for production deployments?: main
            What is the template file path?: template.yaml
            Select an index or enter the stage 1's configuration name (as provided during the bootstrapping): 1
            What is the sam application stack name for stage 1?: sam-app
            What is the pipeline execution role ARN for stage 1?: arn:aws:iam::<TEST ACCOUNT ID>:role/aws-sam-cli-managed-test-pip-PipelineExecutionRole-1DLBUQ6UNNQX7
            What is the CloudFormation execution role ARN for stage 1?: arn:aws:iam::<TEST ACCOUNT ID>:role/aws-sam-cli-managed-test-CloudFormationExecutionR-1BGDI9HEH35O
            What is the S3 bucket name for artifacts for stage 1?: aws-sam-cli-managed-test-pipeline-artifactsbucket-au1hjr2128bw
            What is the ECR repository URI for stage 1?: 
            What is the AWS region for stage 1?: eu-west-3
            Select an index or enter the stage 2's configuration name (as provided during the bootstrapping): 2
            What is the sam application stack name for stage 2?: sam-app
            What is the pipeline execution role ARN for stage 2?: arn:aws:iam::<PROD ACCOUNT ID>:role/aws-sam-cli-managed-prod-pip-PipelineExecutionRole-125II9ETGPTND
            What is the CloudFormation execution role ARN for stage 2?: arn:aws:iam::<PROD ACCOUNT ID>:role/aws-sam-cli-managed-prod-CloudFormationExecutionR-1X9T0LS7UEXZO
            What is the S3 bucket name for artifacts for stage 2?: aws-sam-cli-managed-prod-pipeline-artifactsbucket-204szu1b7wru
            What is the ECR repository URI for stage 2?: 
            What is the AWS region for stage 2?: eu-west-3

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
1. Update your pipeline for Mono repo support
   1. Update `projectA/codepipeline.yaml`
      1. Name your pipeline following sub project folder name (`projectA` here)
         ```
         @@ -116,6 +116,7 @@ Resources:
            Pipeline:
            Type: AWS::CodePipeline::Pipeline
            Properties:
         +      Name: 'projectA'
               ArtifactStore:
                  Location: !Ref PipelineArtifactsBucket
                  Type: S3
         ```
      1. Update pipeline cloudformation template location:
         ```
         @@ -150,7 +151,7 @@ Resources:
                        RoleArn: !GetAtt PipelineStackCloudFormationExecutionRole.Arn
                        StackName: !Ref AWS::StackName
                        ChangeSetName: !Sub ${AWS::StackName}-ChangeSet
         -                TemplatePath: SourceCodeAsZip::codepipeline.yaml
         +                TemplatePath: SourceCodeAsZip::projectA/codepipeline.yaml
                        Capabilities: CAPABILITY_NAMED_IAM
         ```
      1. Update buildspec locations:
         ```
         @@ -579,7 +580,7 @@ Resources:
               ServiceRole: !GetAtt CodeBuildServiceRole.Arn
               Source:
                  Type: CODEPIPELINE
         -        BuildSpec: pipeline/buildspec_feature.yml
         +        BuildSpec: projectA/pipeline/buildspec_feature.yml
         ```
         ```
         @@ -614,7 +615,7 @@ Resources:
               ServiceRole: !GetAtt CodeBuildServiceRole.Arn
               Source:
                  Type: CODEPIPELINE
         -        BuildSpec: pipeline/buildspec_build_package.yml
         +        BuildSpec: projectA/pipeline/buildspec_build_package.yml
         ```
   1. Update buildspec to work in the right folder
      ```
      diff --git a/projectA/pipeline/buildspec_build_package.yml b/projectA/pipeline/buildspec_build_package.yml
      index 537d1d9..bfa6e18 100644
      --- a/projectA/pipeline/buildspec_build_package.yml
      +++ b/projectA/pipeline/buildspec_build_package.yml
      @@ -4,6 +4,7 @@ phases:
         runtime-versions:
            python: 3.8
         commands:
      +      - cd projectA
            - pip install --upgrade pip
            - pip install --upgrade awscli aws-sam-cli
            # Enable docker https://docs.aws.amazon.com/codebuild/latest/userguide/sample-docker-custom-image.html
      @@ -21,6 +22,7 @@ phases:
                           --region ${PROD_REGION}
                           --output-template-file packaged-prod.yaml
      artifacts:
      +  base-directory: projectA
         files:
         - packaged-test.yaml
         - packaged-prod.yaml
      ```
   1. Commit and push to git
      ```
      git add .
      git commit -m "Add pipeline for projectA"
      ```
1. Deploy the pipeline
   ```
   sam deploy -t codepipeline.yaml --stack-name projectA-pipeline --capabilities=CAPABILITY_IAM --profile cicd
   ```
1. Activate the github connection
   1. Go to your CI/CD account console
   1. Got to [Developer tools settings](https://console.aws.amazon.com/codesuite/settings/connections) (if you don't see your connection, check the region you are in)
1. push a new change modifying/creating anything in `projectA` 
1. see it flow through the `projectA` pipeline in CI/CD account

## Setup new subproject

```
sam init projectX
cd projectX
sam pipeline init --bootstrap
# Add Name to pipeline "projectX" and fix path to yamls 
# Disable change detection #TODO
sam deploy -t codepipeline.yaml --stack-name projectX-pipeline --capabilities=CAPABILITY_IAM --profile cicd
```


# TODOs

- [ ] Improve doc around what needs to be edited (codepipeline.yaml vs. folder names, trust relation ship, disable change detection)
- [ ] Test entire procedure
- [ ] Automatically disable change detection in codepipeline
- [ ] Fix trust relationship https://github.com/aws/aws-sam-cli/issues/3857
- [ ] Add common pipeline example

