// App-level провайдери зібрані окремо від entrypoint, щоб:
// 1) тестам було простіше монтувати застосунок із тим самим оточенням;
// 2) main.tsx залишався лише bootstrap-файлом;
// 3) конфігурація глобального server-state жила в одному місці.

import { PropsWithChildren, useState } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

// Підключає глобальні React-провайдери для всього застосунку.
export function AppProviders({ children }: PropsWithChildren) {
  const [queryClient] = useState(
    () =>
      // QueryClient створюємо через lazy useState, а не просто як new QueryClient(...)
      // всередині рендера. Так екземпляр залишається стабільним між rerender-ами
      // і не скидає кеш TanStack Query при кожній зміні React-дерева.
      new QueryClient({
        defaultOptions: {
          queries: {
            // Один retry достатній для тимчасових мережевих збоїв, але не створює
            // надто довгого "мовчазного" очікування в UI.
            retry: 1,
            // Фронтенд тут керує refetch більш явно через invalidateQueries,
            // тому автоматичний refetch on focus вимкнений, щоб не було
            // несподіваних стрибків у формах та management-екранах.
            refetchOnWindowFocus: false
          }
        }
      })
  );

  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
}
