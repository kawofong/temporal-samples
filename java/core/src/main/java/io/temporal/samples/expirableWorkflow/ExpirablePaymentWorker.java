package io.temporal.samples.expirableWorkflow;

import io.temporal.client.WorkflowClient;
import io.temporal.serviceclient.WorkflowServiceStubs;
import io.temporal.worker.Worker;
import io.temporal.worker.WorkerFactory;

/** Worker for the expirable payment workflow. */
public class ExpirablePaymentWorker {

  public static final String TASK_QUEUE = "expirable-payment-queue";

  public static void main(String[] args) {
    // Get a Workflow service stub
    WorkflowServiceStubs service = WorkflowServiceStubs.newLocalServiceStubs();

    // Get a Workflow client
    WorkflowClient client = WorkflowClient.newInstance(service);

    // Create a Worker factory
    WorkerFactory factory = WorkerFactory.newInstance(client);

    // Create a Worker for the task queue
    Worker worker = factory.newWorker(TASK_QUEUE);

    // Register workflow implementation
    worker.registerWorkflowImplementationTypes(ExpirablePaymentWorkflowImpl.class);

    // Register activity implementations
    worker.registerActivitiesImplementations(new PaymentActivitiesImpl());

    // Start the worker
    factory.start();
    System.out.println("\nExpirable Payment Worker started, ctrl+c to exit\n");
  }
}
