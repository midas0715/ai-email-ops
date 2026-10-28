import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CATEGORIES } from "../api/agent";
import type { Category } from "../api/agent";
import {
  createDepartment,
  deleteDepartment,
  listDepartments,
  setDepartmentCategories,
} from "../api/org";
import { ErrorText } from "../components/ErrorText";
import { Field } from "../components/Field";
import { card, dangerButton, primaryButton } from "../components/styles";
import { CATEGORY_NAMES } from "../utils/categories";

const DEPARTMENTS_KEY = ["org", "departments"];

function CategoryChecks({
  value,
  onChange,
  disabled,
}: {
  value: Category[];
  onChange: (next: Category[]) => void;
  disabled?: boolean;
}) {
  return (
    <div className="flex flex-wrap gap-x-4 gap-y-1">
      {CATEGORIES.map((category) => (
        <label key={category} className="flex items-center gap-1.5 text-sm">
          <input
            type="checkbox"
            disabled={disabled}
            checked={value.includes(category)}
            onChange={(event) =>
              onChange(
                event.target.checked
                  ? [...value, category]
                  : value.filter((item) => item !== category),
              )
            }
          />
          {CATEGORY_NAMES[category]}
        </label>
      ))}
    </div>
  );
}

function AddDepartmentForm() {
  const queryClient = useQueryClient();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [categories, setCategories] = useState<Category[]>([]);

  const mutation = useMutation({
    mutationFn: () => createDepartment({ name, email, categories }),
    onSuccess: async () => {
      setName("");
      setEmail("");
      setCategories([]);
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
      <div>
        <p className="mb-1 text-sm font-medium text-slate-700">Handles these categories</p>
        <CategoryChecks value={categories} onChange={setCategories} />
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

  const changeCategories = useMutation({
    mutationFn: (input: { id: number; categories: Category[] }) =>
      setDepartmentCategories(input.id, input.categories),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: DEPARTMENTS_KEY }),
  });

  return (
    <div className="space-y-8">
      <section>
        <h1 className="text-2xl font-semibold">Departments</h1>
        <p className="mt-1 text-sm text-slate-600">
          Tick the categories each department handles. When an agent finishes a ticket, the
          department that matches its category is suggested for the notice email. For example:
          Accounting handles Billing, and Tech handles Technical.
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
                  <th className="px-4 py-3 font-medium">Handles (saved when you tick)</th>
                  <th className="px-4 py-3" />
                </tr>
              </thead>
              <tbody>
                {departments.data.map((department) => (
                  <tr key={department.id} className="border-b border-slate-100 last:border-0">
                    <td className="px-4 py-3">{department.name}</td>
                    <td className="px-4 py-3 text-slate-600">{department.email}</td>
                    <td className="px-4 py-3">
                      <CategoryChecks
                        value={department.categories}
                        disabled={changeCategories.isPending}
                        onChange={(next) =>
                          changeCategories.mutate({ id: department.id, categories: next })
                        }
                      />
                    </td>
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
        <ErrorText error={changeCategories.error} />
        <ErrorText error={remove.error} />
      </section>
    </div>
  );
}