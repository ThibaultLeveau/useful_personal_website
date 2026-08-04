import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { blogBoundary, post } from "./blog-fixtures";
import { BlogManager } from "./blog-manager";

describe("BlogManager", () => {
  it("shows stable identity, lifecycle, taxonomy, and the edit workflow", async () => {
    render(<BlogManager api={blogBoundary()} />);
    expect(await screen.findByRole("heading", { name: "Blog" })).toBeVisible();
    expect(await screen.findByText("Designing a calm API")).toBeVisible();
    expect(screen.getByText("/designing-a-calm-api · rev 2 · 2 min")).toBeVisible();
    expect(screen.getByRole("link", { name: "Edit" })).toHaveAttribute(
      "href",
      `/admin/blog/${post.id}/edit`,
    );
    expect(await screen.findByText("Architecture")).toBeVisible();
  });

  it("passes allow-listed search and lifecycle fields to the generated boundary", async () => {
    const user = userEvent.setup();
    const list = vi.fn(async () => ({
      items: [post],
      pagination: {
        hasNext: false,
        hasPrevious: false,
        page: 1,
        pageSize: 50,
        totalItems: 1,
        totalPages: 1,
      },
    }));
    render(<BlogManager api={blogBoundary({ list })} />);
    await screen.findByText("Designing a calm API");
    await user.type(screen.getByLabelText("Search"), "contract");
    await user.selectOptions(screen.getByLabelText("Lifecycle"), "draft");
    await user.click(screen.getByRole("button", { name: "Apply" }));
    expect(list).toHaveBeenLastCalledWith({ lifecycle: "draft", search: "contract" });
  });
});
