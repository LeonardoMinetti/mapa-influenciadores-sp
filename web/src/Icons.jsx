import React from 'react'

const P = { width: 18, height: 18, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', strokeWidth: 2, strokeLinecap: 'round', strokeLinejoin: 'round', 'aria-hidden': true }
export const IconPin = () => (<svg {...P}><path d="M12 21s-7-6.2-7-11a7 7 0 1 1 14 0c0 4.8-7 11-7 11z" /><circle cx="12" cy="10" r="2.5" /></svg>)
export const IconCheck = () => (<svg {...P}><path d="M20 6 9 17l-5-5" /></svg>)
export const IconChart = () => (<svg {...P}><path d="M4 20V10M10 20V4M16 20v-7M22 20H2" /></svg>)
export const IconSearch = () => (<svg {...P}><circle cx="11" cy="11" r="7" /><path d="m20 20-3.5-3.5" /></svg>)
export const IconHeart = ({ filled }) => (<svg {...P} fill={filled ? 'currentColor' : 'none'}><path d="M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.7l-1-1.1a5.5 5.5 0 0 0-7.8 7.8l1 1.1L12 21l7.8-7.5 1-1.1a5.5 5.5 0 0 0 0-7.8z" /></svg>)
export const IconPlay = () => (<svg {...P} fill="currentColor"><path d="M8 5v14l11-7z" /></svg>)
export const IconExternal = () => (<svg {...P} width="14" height="14"><path d="M14 4h6v6M20 4 10 14M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5" /></svg>)
export const IconBack = () => (<svg {...P}><path d="M15 18 9 12l6-6" /></svg>)
