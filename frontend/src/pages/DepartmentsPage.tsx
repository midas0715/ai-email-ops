import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createDepartment, deleteDepartment, listDepartments } from "../api/org";
import { ErrorText } from "../components/ErrorText";
import { Field } from "../components/Field";
import { card, dangerButton, primaryButton } from "../components/styles";

const DEPARTMENTS_KEY = ["org", "departments"];

function AddDepartmentForm() {
  const queryClient = useQueryClient();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");

  const mutation = useMutation({
    mutationFn: () => createDepartment({ name, email }),
    onSuccess: async () => {
      setName("");
      setEmail("");
      await queryClient.invalidateQueries({ queryKey: DEPARTMENTS_KEY });
    },
  });

  return (
    <form
      className={`${card} space-y-4`}
      onSubmit={(event) => {
        event.preventDefault();
        mutation.mutate();
      }}
    >
      <h2 className="text-lg font-semibold">Add a department</h2>
      <div className="grid gap-4 sm:grid-cols-2">
        <Field
          label="Name (for example Accounting)"
          name="name"
          required
          minLength={2}
          maxLength={100}
          value={name}
          onChange={(event) => setName(event.target.value)}
        />
        <Field
          label="Department email"
          name="email"
          type="email"
          autoComplete="off"
          required
          value={email}
          onChange={(event) => setEmail(event.target.value)}
        />
      </div>
      <ErrorText error={mutation.error} />
      <button type="submit" disabled={mutation.isPending} className={primaryButton}>
        {mutation.isPending ? "Adding..." : "Add department"}
      </button>
    </form>
  );
}

export function DepartmentsPage() {
  const queryClient = useQueryClient();
  const departments = useQuery({ queryKey: DEPARTMENTS_KEY, queryFn: listDepartments });

  const remove = useMutation({
    mutationFn: deleteDepartment,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: DEPARTMENTS_KEY }),
  });

  return (
    <div className="space-y-8">
      <section>
        <h1 className="text-2xl font-semibold">Departments</h1>
        <p className="mt-1 text-sm text-slate-600">
          Agents can escalate a ticket to one of these departments, for example Accounting or HR.
        </p>
      </section>

      <AddDepartmentForm />

      <section className="space-y-3">
        {departments.isPending && <p className="text-slate-500">Loading...</p>}
        <ErrorText error={departments.error} />
        {departments.data && departments.data.length === 0 && (
          <p className="text-slate-500">No departments yet. Add your first one above.</p>
        )}
        {departments.data && departments.data.length > 0 && (
          <div className={`${card} overflow-x-auto p-0`}>
            <table className="w-full text-left text-sm">
              <thead className="border-b border-slate-200 text-slate-500">
                <tr>
                  <th className="px-4 py-3 font-medium">Name</th>
                  <th className="px-4 py-3 font-medium">Email</th>
                  <th className="px-4 py-3" />
                </tr>
              </thead>
              <tbody>
                {departments.data.map((department) => (
                  <tr key={department.id} className="border-b border-slate-100 last:border-0">
                    <td className="px-4 py-3">{department.name}</td>
                    <td className="px-4 py-3 text-slate-600">{department.email}</td>
                    <td className="px-4 py-3 text-right">
                      <button
                        className={dangerButton}
                        disabled={remove.isPending}
                        onClick={() => {
                          if (window.confirm(`Delete the ${department.name} department?`)) {
                            remove.mutate(department.id);
                          }
                        }}
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        <ErrorText error={remove.error} />
      </section>
    </div>
  );
}