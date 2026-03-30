import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  completeSchedule,
  getMyClasses,
  getScheduleAttendees,
  getSchedules,
  queryKeys
} from "../../../shared/api";

type UseClassesPageDataOptions = {
  isManagement: boolean;
  selectedClassId: string | null;
};

// Виносить server-state та invalidation policy з page-компонента, щоб JSX лишався
// про рендер, а не про fetch/mutation wiring.
export function useClassesPageData({
  isManagement,
  selectedClassId
}: UseClassesPageDataOptions) {
  const queryClient = useQueryClient();

  // Менеджмент бачить весь клубний потік занять, тренер — лише свої.
  const classesQuery = useQuery({
    queryKey: isManagement ? queryKeys.classes.all() : queryKeys.classes.mine(),
    queryFn: () => (isManagement ? getSchedules() : getMyClasses())
  });

  // Деталі учасників потрібні лише для вибраного заняття з правої панелі.
  const attendeesQuery = useQuery({
    queryKey: queryKeys.classes.attendees(selectedClassId),
    queryFn: () => getScheduleAttendees(selectedClassId as string),
    enabled: Boolean(selectedClassId)
  });

  const completeMutation = useMutation({
    mutationFn: ({ classId, comment }: { classId: string; comment: string }) =>
      completeSchedule(classId, { comment }),
    onSuccess: () => {
      // Після завершення заняття оновлюємо всі поверхні, які читають цей самий зріз даних.
      // Це не лише classes page: dashboard і загальний schedule теж показують цей клас.
      queryClient.invalidateQueries({ queryKey: queryKeys.classes.mine() });
      queryClient.invalidateQueries({ queryKey: queryKeys.classes.all() });
      queryClient.invalidateQueries({ queryKey: queryKeys.schedules.all() });
      queryClient.invalidateQueries({ queryKey: queryKeys.dashboard.myClasses() });
      queryClient.invalidateQueries({ queryKey: queryKeys.dashboard.schedules() });
    }
  });

  return {
    classesQuery,
    attendeesQuery,
    completeMutation
  };
}
