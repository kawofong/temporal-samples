# Java samples

## Pre-requisites

- [sdkman](https://sdkman.io/install/)
- [Java JDK](https://sdkman.io/jdks)

## Getting started

To run a Java workflow, run the following command in your terminal.

    ```bash
    ./run_workflow.sh <fully-qualified-workflow-name-in-core>
    ```

For example, you would use the following command to run the [`HelloActivity`](./core/src/main/java/io/temporal/samples/hello/HelloActivity.java).

    ```bash
    ./run_workflow.sh io.temporal.samples.hello.HelloActivity
    ```

Or you can use `gradlew`. To run the [`ExpirableWorkflowWorker`](./core/src/main/java/io/temporal/samples/expirableWorkflow/ExpirablePaymentWorker.java), run:

    ```bash
    ./gradlew :core:execute -PmainClass=io.temporal.samples.expirableWorkflow.ExpirablePaymentWorker
    ```