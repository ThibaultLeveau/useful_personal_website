import type { PublicSkillData } from "@/generated/api/src/models";

import styles from "./skills.module.css";

interface CategoryGroup {
  description: string | null;
  name: string;
  position: number;
  skills: PublicSkillData[];
  slug: string;
}

export function groupSkills(skills: PublicSkillData[]): CategoryGroup[] {
  const groups = new Map<string, CategoryGroup>();
  for (const skill of skills) {
    const current = groups.get(skill.categorySlug);
    if (current) current.skills.push(skill);
    else {
      groups.set(skill.categorySlug, {
        description: skill.categoryDescription,
        name: skill.categoryName,
        position: skill.categoryPosition,
        skills: [skill],
        slug: skill.categorySlug,
      });
    }
  }
  return [...groups.values()].sort(
    (left, right) => left.position - right.position || left.slug.localeCompare(right.slug),
  );
}

export function PublicSkills({ skills }: { skills: PublicSkillData[] }) {
  const groups = groupSkills(skills);
  if (!groups.length) {
    return (
      <section className={styles.empty} role="status">
        <p className="eyebrow">No matches</p>
        <h2>No published skills match these filters.</h2>
        <p>Clear a filter to see the complete capability map.</p>
      </section>
    );
  }
  return (
    <div className={styles.groups}>
      {groups.map((group) => (
        <section className={styles.group} id={group.slug} key={group.slug}>
          <header>
            <p className="eyebrow">Category {String(group.position + 1).padStart(2, "0")}</p>
            <h2>{group.name}</h2>
            {group.description ? <p>{group.description}</p> : null}
          </header>
          <ul className={styles.grid}>
            {group.skills.map((skill) => (
              <li className={styles.card} key={skill.slug}>
                <div className={styles.cardHeading}>
                  <h3>{skill.name}</h3>
                  {skill.featured ? <span className={styles.featured}>Featured</span> : null}
                </div>
                {skill.description ? <p>{skill.description}</p> : null}
                <dl className={styles.facts}>
                  {skill.proficiencyLabel ? (
                    <div>
                      <dt>Level</dt>
                      <dd>{skill.proficiencyLabel}</dd>
                    </div>
                  ) : null}
                  <div>
                    <dt>Experience</dt>
                    <dd>{skill.yearsExperience} years</dd>
                  </div>
                </dl>
                {skill.proficiencyScore !== null ? (
                  <div className={styles.meter}>
                    <span>Proficiency</span>
                    <progress
                      aria-label={`${skill.name} proficiency`}
                      max={100}
                      value={skill.proficiencyScore}
                    />
                    <span>{skill.proficiencyScore}/100</span>
                  </div>
                ) : null}
              </li>
            ))}
          </ul>
        </section>
      ))}
    </div>
  );
}
