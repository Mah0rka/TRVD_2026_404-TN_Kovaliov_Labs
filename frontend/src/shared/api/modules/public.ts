import type { ClubStats } from "../core/contracts";
import { clubStatsSchema } from "../core/contracts";
import { request } from "../core/http";

export async function getClubStats(): Promise<ClubStats> {
  const data = await request<unknown>("/public/club-stats", { method: "GET" });
  return clubStatsSchema.parse(data);
}
