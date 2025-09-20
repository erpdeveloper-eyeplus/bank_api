## Bank API

Bank API Integration

### 📌 Custom Bank API App – Overview

This custom app integrates with the **Bank’s Eazypay API** for handling payment requests and responses.

### 🔹 Bank API Log Doctype

* **Purpose**: Central log for all communication with the Bank.
* **Usage**:

  1. **Request Creation** – When a payment request is generated (e.g., from a **Sales Order**), a new entry is created in **Bank API Log** with a **Reference ID**.
  2. **Response Handling** – Once the customer pays, the **bank’s response** (success/failure status, transaction details) is updated against the same **Bank API Log** record.
  3. Provides **traceability** for both **outgoing requests** and **incoming responses**.


### 🔹 Development Flow

1. **Reference ID Generation**

   * On Sales Order confirmation, system generates a unique **Reference ID**.
   * This ID is stored in **Bank API Log**.

2. **Bank Request (via Eazypay API)**

   * Request payload is built and sent to the Bank API using the **Eazypay SDK** (in `src/eazypay`).
   * Log entry is updated with **Request Data** and **Reference ID**.

3. **Bank Response Update**

   * Bank responds with **transaction details** (success/failure).
   * This response is parsed and **updated back** into the same **Bank API Log** entry.

4. **Sales Order Linking**

   * Once payment is confirmed, **Sales Order** is automatically updated against the Bank API Log entry.
   * Ensures customer payments are traceable against Sales Orders.


### 🔹 `src` Folder (Bank-Side Code)

* The `src/eazypay` folder contains the **bank-provided SDK code**.
* This acts as the **main integration layer** – whenever the bank updates their API SDK, this folder must be replaced/updated.
* Custom app dynamically imports from `src/eazypay` for request/response handling.


* **src/eazypay** = Bank-provided code that must always stay updated with their changes.


#### License

mit