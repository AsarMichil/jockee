import RootPlayer from "../RootPlayer";

export default function PlayerLayout({
  children
}: {
  children: React.ReactNode;
}) {
  return (
    <>
      <RootPlayer />
      {children}
    </>
  );
}
