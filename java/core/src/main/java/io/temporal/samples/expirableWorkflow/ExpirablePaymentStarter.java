package io.temporal.samples.expirableWorkflow;

import io.temporal.client.WorkflowClient;
import io.temporal.client.WorkflowOptions;
import io.temporal.serviceclient.WorkflowServiceStubs;
import java.util.UUID;

/**
 * Workflow starter for the expirable payment workflow.
 *
 * <p>This demonstrates starting the workflow with different expiration times:
 *
 * <ul>
 *   <li>A workflow that completes before expiration
 *   <li>A workflow that expires before completion
 * </ul>
 */
public class ExpirablePaymentStarter {

  public static void main(String[] args) {
    // Get a Workflow service stub
    WorkflowServiceStubs service = WorkflowServiceStubs.newLocalServiceStubs();

    // Get a Workflow client
    WorkflowClient client = WorkflowClient.newInstance(service);

    System.out.println("\n############################################################");
    System.out.println("# Expirable Payment Workflow Demo");
    System.out.println("############################################################");

    // Demo 1: Workflow completes before expiration
    demoSuccessfulCompletion(client);

    // Demo 2: Workflow expires before completion
    demoExpiration(client);
  }

  /**
   * Demo: Workflow completes before expiration.
   *
   * <p>The payment processing takes ~4 seconds total, so with a 10-second expiration, it should
   * complete successfully.
   */
  private static void demoSuccessfulCompletion(WorkflowClient client) {
    System.out.println("\n============================================================");
    System.out.println("DEMO 1: Workflow that completes before expiration");
    System.out.println("============================================================");

    runWorkflow(client, 10, 100.0);
  }

  /**
   * Demo: Workflow expires before completion.
   *
   * <p>The payment processing takes ~4 seconds total, so with a 3-second expiration, it should
   * expire before completing.
   */
  private static void demoExpiration(WorkflowClient client) {
    System.out.println("\n============================================================");
    System.out.println("DEMO 2: Workflow that expires before completion");
    System.out.println("============================================================");

    runWorkflow(client, 3, 100.0);
  }

  /**
   * Start and run an expirable payment workflow.
   *
   * @param client the workflow client
   * @param expireIn number of seconds until the workflow expires
   * @param amount payment amount
   */
  private static void runWorkflow(WorkflowClient client, int expireIn, double amount) {
    String paymentId = "PAY-" + UUID.randomUUID().toString().substring(0, 8);

    PaymentWorkflowInput input = new PaymentWorkflowInput(paymentId, amount, expireIn);

    System.out.println("\n============================================================");
    System.out.println("Starting workflow: " + paymentId);
    System.out.println("Amount: $" + String.format("%.2f", amount));
    System.out.println("Expiration: " + expireIn + " seconds");
    System.out.println("============================================================\n");

    // Create the workflow stub
    ExpirablePaymentWorkflow workflow =
        client.newWorkflowStub(
            ExpirablePaymentWorkflow.class,
            WorkflowOptions.newBuilder()
                .setWorkflowId("expirable-payment-" + paymentId)
                .setTaskQueue(ExpirablePaymentWorker.TASK_QUEUE)
                .build());

    // Execute the workflow synchronously
    PaymentWorkflowResult result = workflow.processPayment(input);

    System.out.println("\n============================================================");
    System.out.println("Workflow completed!");
    System.out.println("Payment ID: " + result.getPaymentId());
    System.out.println("Status: " + result.getStatus());
    System.out.println("Message: " + result.getMessage());
    System.out.println("============================================================\n");
  }
}
