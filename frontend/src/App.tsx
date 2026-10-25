import { Route, Routes } from "react-router";
import { RequireRole } from "./auth/RequireRole";
import { Layout } from "./components/Layout";
import { AgentHome } from "./pages/AgentHome";
import { CeoHome } from "./pages/CeoHome";
import { Home } from "./pages/Home";
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
          <Route path="/ceo" element={<CeoHome />} />
        </Route>
        <Route element={<RequireRole role="agent" />}>
          <Route path="/agent" element={<AgentHome />} />
        </Route>

        <Route path="*" element={<p className="text-slate-600">Page not found.</p>} />
      </Route>
    </Routes>
  );
}