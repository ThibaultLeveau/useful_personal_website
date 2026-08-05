import { describe, expect, it } from "vitest";
import { BLOCK_TYPES, newBlock } from "./block-catalog";

describe("page block catalog", () => {
  it("builds one strict current-version draft template for every frozen kind", () => {
    expect(BLOCK_TYPES).toHaveLength(19);
    for (const type of BLOCK_TYPES) {
      const block = newBlock(
        type,
        type === "image" || type === "image_with_text"
          ? "0198a13d-8300-7000-8000-000000000001"
          : undefined,
      );
      expect(block.blockType).toBe(type);
      expect(block.schemaVersion).toBe(1);
      expect(block.visible).toBe(true);
      expect(block.config).toBeTruthy();
    }
  });
});
