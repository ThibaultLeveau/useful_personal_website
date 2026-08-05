import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { AdminMediaApiBoundary } from "@/features/media/admin-api";

import type { AdminProjectsApiBoundary } from "./admin-api";
import { ProjectEditor } from "./project-editor";
import { fixtureProject, projectBoundary } from "./project-fixtures";

const push = vi.fn();
const mediaApi: AdminMediaApiBoundary = {
  delete: vi.fn(),
  list: vi.fn(async () => ({
    items: [],
    pagination: {
      page: 1,
      pageSize: 100,
      hasNext: false,
      hasPrevious: false,
      totalItems: 0,
      totalPages: 0,
    },
  })),
  rename: vi.fn(),
  upload: vi.fn(),
  usage: vi.fn(async () => []),
};
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push, refresh: vi.fn() }),
}));

describe("project editor", () => {
  beforeEach(() => push.mockClear());

  it("retains complete case-study input and saves through the typed API seam", async () => {
    const user = userEvent.setup();
    const save = vi.fn<AdminProjectsApiBoundary["save"]>(async (item, input) => ({
      ...item,
      draft: { ...item.draft, ...input },
      version: 2,
    }));
    render(
      <ProjectEditor
        api={projectBoundary({ save })}
        mediaApi={mediaApi}
        projectId={fixtureProject.id}
      />,
    );
    expect(await screen.findByRole("heading", { name: "API Platform", level: 1 })).toBeVisible();
    expect(screen.getByRole("group", { name: "Project cover" })).toBeVisible();
    expect(screen.getByRole("group", { name: "Add screenshot" })).toBeVisible();
    expect(screen.getByLabelText("Schedule in Europe/Paris")).toHaveAttribute(
      "type",
      "datetime-local",
    );

    const name = screen.getByRole("textbox", { name: "Project name" });
    await user.clear(name);
    await user.type(name, "API Platform evolved");
    await user.click(screen.getByRole("button", { name: "Save project" }));

    await waitFor(() => expect(save).toHaveBeenCalledOnce());
    expect(save.mock.calls[0]?.[1]).toEqual(
      expect.objectContaining({
        coverMediaId: null,
        name: "API Platform evolved",
        screenshotMediaIds: [],
        technologies: ["Python", "PostgreSQL"],
      }),
    );
    expect(screen.getByRole("status")).toHaveTextContent("Project saved");
    expect(push).not.toHaveBeenCalled();
  });

  it("keeps visibility, featured state, and publication as separate actions", async () => {
    const user = userEvent.setup();
    const publish = vi.fn<AdminProjectsApiBoundary["publish"]>(async (item) => ({
      ...item,
      lifecycle: "published",
      published: item.draft,
      version: 2,
    }));
    const setFeatured = vi.fn<AdminProjectsApiBoundary["setFeatured"]>(async (item, featured) => ({
      ...item,
      featured,
      version: item.version + 1,
    }));
    const setVisibility = vi.fn<AdminProjectsApiBoundary["setVisibility"]>(
      async (item, visible) => ({ ...item, visible, version: item.version + 1 }),
    );
    render(
      <ProjectEditor
        api={projectBoundary({ publish, setFeatured, setVisibility })}
        mediaApi={mediaApi}
        projectId={fixtureProject.id}
      />,
    );
    await screen.findByRole("heading", { name: "API Platform", level: 1 });
    await user.click(screen.getByRole("button", { name: "Hide" }));
    await waitFor(() => expect(setVisibility).toHaveBeenCalledWith(fixtureProject, false));
    await user.click(screen.getByRole("button", { name: "Unfeature" }));
    await waitFor(() => expect(setFeatured).toHaveBeenCalled());
    await user.click(screen.getByRole("button", { name: "Publish now" }));
    await waitFor(() => expect(publish).toHaveBeenCalled());
  });
});
