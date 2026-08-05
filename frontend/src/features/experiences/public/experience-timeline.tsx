import type { Route } from "next";
import Link from "next/link";

import type { PublicExperienceData } from "@/generated/api/src/models";

import styles from "./experiences.module.css";

const employmentLabels: Record<PublicExperienceData["employmentType"], string> = {
  apprenticeship: "Apprenticeship",
  contract: "Contract",
  freelance: "Freelance",
  full_time: "Full time",
  internship: "Internship",
  part_time: "Part time",
  seasonal: "Seasonal",
  temporary: "Temporary",
  volunteer: "Volunteer",
};

const remoteLabels: Record<PublicExperienceData["remoteStatus"], string> = {
  hybrid: "Hybrid",
  onsite: "On-site",
  remote: "Remote",
};

const month = new Intl.DateTimeFormat("en", {
  month: "short",
  timeZone: "UTC",
  year: "numeric",
});

export function experienceDateRange(item: PublicExperienceData): string {
  const start = month.format(item.startDate);
  if (item.currentPosition) return `${start} – Present`;
  return item.endDate ? `${start} – ${month.format(item.endDate)}` : `${start} – End date open`;
}

export function ExperienceTimeline({ experiences }: { experiences: PublicExperienceData[] }) {
  if (!experiences.length) {
    return (
      <section className={styles.empty} role="status">
        <p className="eyebrow">Experience</p>
        <h2>No published experience matches these filters.</h2>
        <p>Clear the filters to return to the full chronology.</p>
      </section>
    );
  }

  return (
    <ol className={styles.timeline} aria-label="Professional experience chronology">
      {experiences.map((item, index) => (
        <li className={styles.entry} key={item.id}>
          <span className={styles.rail} aria-hidden="true" />
          <article aria-labelledby={`experience-${item.id}`}>
            <p className={styles.sequence} aria-hidden="true">
              {String(index + 1).padStart(2, "0")}
            </p>
            <header className={styles.heading}>
              <div>
                <p className="eyebrow">{experienceDateRange(item)}</p>
                <h2 id={`experience-${item.id}`}>{item.roleTitle}</h2>
                <p className={styles.company}>
                  {item.companyUrl ? (
                    <a href={item.companyUrl} rel="noopener noreferrer">
                      {item.companyName}
                    </a>
                  ) : (
                    item.companyName
                  )}
                </p>
              </div>
              <dl className={styles.facts}>
                <div>
                  <dt>Engagement</dt>
                  <dd>{employmentLabels[item.employmentType]}</dd>
                </div>
                <div>
                  <dt>Work style</dt>
                  <dd>{remoteLabels[item.remoteStatus]}</dd>
                </div>
                {item.location ? (
                  <div>
                    <dt>Location</dt>
                    <dd>{item.location}</dd>
                  </div>
                ) : null}
              </dl>
            </header>
            <p className={styles.summary}>{item.shortSummary}</p>
            {item.detailedDescription ? (
              <p className={styles.description}>{item.detailedDescription}</p>
            ) : null}
            <div className={styles.details}>
              {item.achievements.length ? (
                <section>
                  <h3>Selected outcomes</h3>
                  <ul>
                    {item.achievements.map((achievement) => (
                      <li key={achievement}>{achievement}</li>
                    ))}
                  </ul>
                </section>
              ) : null}
              {item.responsibilities.length ? (
                <section>
                  <h3>Responsibilities</h3>
                  <ul>
                    {item.responsibilities.map((responsibility) => (
                      <li key={responsibility}>{responsibility}</li>
                    ))}
                  </ul>
                </section>
              ) : null}
            </div>
            {item.technologies.length || item.skills.length ? (
              <footer className={styles.evidence}>
                {item.technologies.map((technology) => (
                  <span key={technology}>{technology}</span>
                ))}
                {item.skills.map((skill) => (
                  <Link href={`/skills#${skill.slug}` as Route} key={skill.slug}>
                    {skill.name}
                  </Link>
                ))}
              </footer>
            ) : null}
          </article>
        </li>
      ))}
    </ol>
  );
}
