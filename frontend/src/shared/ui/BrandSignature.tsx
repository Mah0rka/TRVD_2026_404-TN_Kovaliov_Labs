import brandLogo from "../../assets/logo/logo.png";

type BrandSignatureProps = {
  subtitle: string;
};

// Показує бренд-блок із назвою та підзаголовком клубу.
export function BrandSignature({ subtitle }: BrandSignatureProps) {
  return (
    <div className="brand-signature">
      <img className="brand-logo" src={brandLogo} alt="Логотип MotionLab" />
      <div className="brand-copy">
        <div className="brand-title">MotionLab</div>
        <div className="brand-subtitle">{subtitle}</div>
      </div>
    </div>
  );
}
