import api from "./axios";

export const getReminderStatus = async () => {
  const response = await api.get("/reminders/status");
  return response.data;
};

export const testSmtp = async (to_email) => {
  const response = await api.post("/reminders/test-smtp", { to_email });
  return response.data;
};

export const triggerDueCheck = async (force = false) => {
  const response = await api.post(`/reminders/trigger-check?force=${force}`);
  return response.data;
};

export const sendTransactionReminder = async (transactionId, notificationType = "manual") => {
  const response = await api.post(
    `/reminders/send-transaction/${transactionId}?notification_type=${notificationType}`
  );
  return response.data;
};

export const getReminderLogs = async (params = {}) => {
  const response = await api.get("/reminders/logs", { params });
  return response.data;
};
