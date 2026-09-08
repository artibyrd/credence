/**
 * Credence Workstation Universal Topics Aggregator
 * Zero-npm native ES module.
 */

import { REPORTS_TOPICS } from './topics/reports.js';
import { FOUNDATION_TOPICS } from './topics/foundation.js';
import { NEXUS_TOPICS } from './topics/nexus.js';

export const INFO_TOPICS = {
  ...REPORTS_TOPICS,
  ...FOUNDATION_TOPICS,
  ...NEXUS_TOPICS,
};

export { REPORTS_TOPICS, FOUNDATION_TOPICS, NEXUS_TOPICS };
