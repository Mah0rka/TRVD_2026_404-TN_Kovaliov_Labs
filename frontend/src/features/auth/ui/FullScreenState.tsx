// Коротко: компонент керує UI-логікою для модуля повноекранного стану.

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
