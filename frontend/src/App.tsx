import { Route, Routes } from "react-router";
import { RequireRole } from "./auth/RequireRole";
import { CeoLayout } from "./components/CeoLayout";
import { Layout } from "./components/Layout";
import { AgentsPage } from "./pages/AgentsPage";
import { ApiKeyPage } from "./pages/ApiKeyPage";
import { CeoHome } from "./pages/CeoHome";
import { DepartmentsPage } from "./pages/DepartmentsPage";
import { DocumentsPage } from "./pages/DocumentsPage";
import { EmailPage } from "./pages/EmailPage";
import { Home } from "./pages/Home";
import { InboxPage } from "./pages/InboxPage";
import { LoginPage } from "./pages/LoginPage";
import { RegisterOrg } from "./pages/RegisterOrg";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Home />} />
        <Route path="/ceo/register" element={<RegisterOrg />} />
        <Route path="/ceo/login" element={<LoginPage role="org" />} />
        <Route path="/agent/login" element={<LoginPage role="agent" />} />

        <Route element={<RequireRole role="org" />}>
          <Route path="/ceo" element={<CeoLayout />}>
            <Route index element={<CeoHome />} />
            <Route path="agents" element={<AgentsPage />} />
            <Route path="departments" element={<DepartmentsPage />} />
            <Route path="documents" element={<DocumentsPage />} />
            <Route path="api-key" element={<ApiKeyPage />} />
          </Route>
        </Route>

        <Route element={<RequireRole role="agent" />}>
          <Route path="/agent" element={<InboxPage />} />
          <Route path="/agent/emails/:emailId" element={<EmailPage />} />
        </Route>

        <Route path="*" element={<p className="text-slate-600">Page not found.</p>} />
      </Route>
    </Routes>
  );
}