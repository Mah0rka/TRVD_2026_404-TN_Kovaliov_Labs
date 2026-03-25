// Модуль містить виклики API для конкретної предметної області.

import { z } from "zod";

import type { Booking } from "../core/contracts";
import { bookingSchema } from "../core/contracts";
import type { Payment } from "../core/contracts";
import { paymentSchema } from "../core/contracts";
import { request } from "../core/http";

// Отримує бронювання поточного користувача.
export async function getMyBookings(): Promise<Booking[]> {
  const data = await request<unknown>("/bookings/my-bookings", { method: "GET" });
  return z.array(bookingSchema).parse(data);
}

// Створює booking.
export async function createBooking(classId: string): Promise<Booking> {
  const data = await request<unknown>(`/bookings/${classId}`, { method: "POST" });
  return bookingSchema.parse(data);
}

// Запускає checkout для платного бронювання заняття.
export async function createPaidBookingCheckout(classId: string): Promise<Payment> {
  const data = await request<unknown>(`/bookings/${classId}/checkout`, { method: "POST" });
  return paymentSchema.parse(data);
}

// Підтверджує платний запис після успішного checkout.
export async function confirmPaidBooking(paymentId: string): Promise<Booking> {
  const data = await request<unknown>(`/bookings/payments/${paymentId}/confirm`, { method: "POST" });
  return bookingSchema.parse(data);
}

// Обслуговує сценарій cancel booking.
export async function cancelBooking(bookingId: string): Promise<Booking> {
  const data = await request<unknown>(`/bookings/${bookingId}/cancel`, { method: "PATCH" });
  return bookingSchema.parse(data);
}
