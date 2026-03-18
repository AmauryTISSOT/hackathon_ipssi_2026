import AppLayout from "../components/AppLayout";
import UploadPanel from "../components/UploadPanel";
import { getCurrentUser } from "../services/authApi";
import { createDocument } from "../services/documentApi";

const userLinks = [
  { to: "/user/recap", label: "Historique des depots" },
  { to: "/user/depot", label: "Deposer un document" }
];

function ClientUploadPage() {
  const currentUser = getCurrentUser();

  const handleAdd = async ({ file }) => {
    if (!currentUser) {
      throw new Error("Session invalide. Merci de vous reconnecter.");
    }

    return createDocument({ file });
  };

  return (
    <AppLayout title="Depot de document" links={userLinks}>
      <UploadPanel onSubmit={handleAdd} />
    </AppLayout>
  );
}

export default ClientUploadPage;
