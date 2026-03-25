// Коротко: модуль виконує API-запити для модуля бронювань.

import { z } from "zod";

import type { Booking } from "../core/contracts";
import { bookingSchema } from "../core/contracts";
import type { Payment } from "../core/contracts";
import { paymentSchema } from "../core/contracts";
import { request } from "../core/http";

export async function getMyBookings(): Promise<Booking[]> {
  const data = await request<unknown>("/bookings/my-bookings", { method: "GET" });
  return z.array(bookingSchema).parse(data);
}

export async function createBooking(classId: string): Promise<Booking> {
  const data = await request<unknown>(`/bookings/${classId}`, { method: "POST" });
  return bookingSchema.parse(data);
}

export async function createPaidBookingCheckout(classId: string): Promise<Payment> {
  const data = await request<unknown>(`/bookings/${classId}/checkout`, { method: "POST" });
  return paymentSchema.parse(data);
}

export async function confirmPaidBooking(paymentId: string): Promise<Booking> {
  const data = await request<unknown>(`/bookings/payments/${paymentId}/confirm`, { method: "POST" });
  return bookingSchema.parse(data);
}

export async function cancelBooking(bookingId: string): Promise<Booking> {
  const data = await request<unknown>(`/bookings/${bookingId}/cancel`, { method: "PATCH" });
  return bookingSchema.parse(data);
}
