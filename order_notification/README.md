# Order Notification

This workflow manages a pick up order for users. The user places an order through
a food ordering application and the vendor prepares the order.

## State machine

```mermaid
stateDiagram-v2
    [*] --> OrderPlaced
    OrderPlaced --> VendorNotified: Send push/SMS to vendor
    VendorNotified --> OrderAccepted: Vendor accepts
    VendorNotified --> OrderDeclined: Vendor declines/timeout

    state OrderExpiration {
        OrderAccepted --> OrderPreparation: Vendor starts preparation
        OrderAccepted --> OrderReady: Vendor timeouts
        OrderPreparation --> OrderReady: Vendor marks ready

        OrderDeclined
    }
    OrderReady --> OrderPickedUp
    OrderDeclined --> [*]
    OrderPickedUp --> [*]
```

## Getting started

From the root directory of the project, use `uv` to run a workflow runner:

```bash
uv run -m order_notification.runners.workflow
```
