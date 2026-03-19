import AppLayout from "../components/AppLayout";
import UploadPanel from "../components/UploadPanel";
import { getCurrentUser } from "../services/authApi";
import { createDocument } from "../services/documentApi";

const comptableLinks = [
  { to: "/comptable/gestion", label: "Gestion des documents" },
  { to: "/comptable/depot", label: "Deposer un document" }
];

function ComptableUploadPage() {
  const currentUser = getCurrentUser();

  const handleAdd = async ({ file }) => {
    if (!currentUser) {
      throw new Error("Session invalide. Merci de vous reconnecter.");
    }

    return createDocument({ file });
  };

  return (
    <AppLayout title="Analyse de document" links={comptableLinks}>
      <UploadPanel onSubmit={handleAdd} />
    </AppLayout>
  );
}

export default ComptableUploadPage;
