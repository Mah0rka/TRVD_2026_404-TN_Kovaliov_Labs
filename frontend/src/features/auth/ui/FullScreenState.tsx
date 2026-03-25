// Компонент інкапсулює частину UI-логіки конкретної фічі.

// Показує повноекранний стан очікування або повідомлення.
export function FullScreenState({ message }: { message: string }) {
  return (
    <main className="screen">
      <section className="card auth-card">
        <p className="eyebrow">MotionLab</p>
        <h1>{message}</h1>
      </section>
    </main>
  );
}
