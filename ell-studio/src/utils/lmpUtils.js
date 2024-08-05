import axios from 'axios';


export const aggregateLMPsByName = (lmpList) => {
  const lmpsByName = new Map()
  const lmpNameById = new Map()
  lmpList.forEach(lmp => {
    const cleanedLmp = {
      ...lmp,
      created_at: new Date(lmp.created_at + 'Z'),
    }
    if (!lmpsByName.has(lmp.name)) {
      lmpsByName.set(lmp.name, [cleanedLmp]);
    } else {
      lmpsByName.get(lmp.name).push(cleanedLmp);
    }
    lmpNameById.set(lmp.lmp_id, lmp.name)
  });

  const latestLMPByName = new Map()
  lmpsByName.forEach((lmpVersions, lmpName) => {
    const latestLMP = lmpVersions.sort((a, b) => b.created_at - a.created_at)[0]
    latestLMPByName.set(lmpName, latestLMP)
  })

  // Now make a latest LMP by nam but add all the versions as a property on that lmp
  const latestLMPs = Array.from(latestLMPByName.values())
  latestLMPs.forEach(lmp => {
    lmp.versions = lmpsByName.get(lmp.name).sort((a, b) => b.created_at - a.created_at)
    // sanetize the uses of the lmp to only have the latest version of the lmp whose id has that name
    lmp.uses = lmp.uses.map(useId => {
      const useLmpName = lmpNameById.get(useId)
      return latestLMPByName.get(useLmpName).lmp_id
    })
  })
  
  return latestLMPs
};



export function getTimeAgo(date) {
  const now = new Date();
  const secondsPast = (now.getTime() - date.getTime()) / 1000;
  if (secondsPast < 60) {
    return `${Math.round(secondsPast)} seconds ago`;
  }
  if (secondsPast < 3600) {
    return `${Math.round(secondsPast / 60)} minutes ago`;
  }
  if (secondsPast <= 86400) {
    return `${Math.round(secondsPast / 3600)} hours ago`;
  }
  if (secondsPast <= 2592000) {
    return `${Math.round(secondsPast / 86400)} days ago`;
  }
  if (secondsPast <= 31536000) {
    return `${Math.round(secondsPast / 2592000)} months ago`;
  }
  return `${Math.round(secondsPast / 31536000)} years ago`;
}

