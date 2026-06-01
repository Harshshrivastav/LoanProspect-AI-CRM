// src/hooks/useClientPortal.js
import { useState, useEffect, useCallback } from "react";
import {
  getCustomer,
  getProspect,
  getTransactions,
  generateMessage,
  approveMessage,
} from "../api/client";

export function useClientPortal(customerId) {
  const [customer, setCustomer] = useState(null);
  const [prospect, setProspect] = useState(null);
  const [transactions, setTransactions] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Unified message generation and sending state
  const [messageState, setMessageState] = useState({
    tone: "friendly",
    channel: "whatsapp",
    productType: "personal_loan",
    generating: false,
    generated: false,
    editedText: "",
    approving: false,
    approved: false,
    error: null,
    outreachId: null,
  });

  const load = useCallback(async () => {
    if (!customerId) return;
    setLoading(true);
    setError(null);
    setCustomer(null);
    setProspect(null);
    setTransactions(null);
    
    // Reset message state when customer changes
    setMessageState({
      tone: "friendly",
      channel: "whatsapp",
      productType: "personal_loan",
      generating: false,
      generated: false,
      editedText: "",
      approving: false,
      approved: false,
      error: null,
      outreachId: null,
    });

    try {
      const [cust, pros, txns] = await Promise.allSettled([
        getCustomer(customerId),
        getProspect(customerId),
        getTransactions(customerId, 90),
      ]);
      if (cust.status === "fulfilled") setCustomer(cust.value);
      else setError(cust.reason?.message);
      if (pros.status === "fulfilled") setProspect(pros.value);
      if (txns.status === "fulfilled") setTransactions(txns.value);
    } finally {
      setLoading(false);
    }
  }, [customerId]);

  useEffect(() => {
    load();
  }, [load]);

  const updateMessageConfig = useCallback((key, value) => {
    setMessageState((prev) => ({
      ...prev,
      [key]: value,
      // If tone, channel, or productType changes, reset the generated message
      ...(key === "tone" || key === "channel" || key === "productType"
        ? { generated: false, approved: false, editedText: "", outreachId: null, error: null }
        : {}),
    }));
  }, []);

  const updateEditedText = useCallback((text) => {
    setMessageState((prev) => ({ ...prev, editedText: text }));
  }, []);

  const handleGenerateMessage = useCallback(async () => {
    if (!customerId) return;
    setMessageState((prev) => ({
      ...prev,
      generating: true,
      error: null,
      approved: false,
      generated: false,
    }));
    try {
      const res = await generateMessage(
        customerId,
        messageState.productType,
        messageState.tone,
        messageState.channel
      );
      setMessageState((prev) => ({
        ...prev,
        generating: false,
        generated: true,
        editedText: res.message_text || res.message || "",
        outreachId: res.outreach_id || null,
      }));
    } catch (err) {
      setMessageState((prev) => ({
        ...prev,
        generating: false,
        error: err.message,
      }));
    }
  }, [customerId, messageState.productType, messageState.tone, messageState.channel]);

  const handleApproveMessage = useCallback(async () => {
    if (!messageState.outreachId) {
      setMessageState((prev) => ({
        ...prev,
        error: "No active message to approve. Please generate one first.",
      }));
      return;
    }
    setMessageState((prev) => ({ ...prev, approving: true, error: null }));
    try {
      await approveMessage(messageState.outreachId);
      setMessageState((prev) => ({
        ...prev,
        approving: false,
        approved: true,
      }));
    } catch (err) {
      setMessageState((prev) => ({
        ...prev,
        approving: false,
        error: err.message,
      }));
    }
  }, [messageState.outreachId]);

  return {
    customer,
    prospect,
    transactions,
    loading,
    error,
    refetch: load,
    messageState,
    handleGenerateMessage,
    handleApproveMessage,
    updateMessageConfig,
    updateEditedText,
  };
}
