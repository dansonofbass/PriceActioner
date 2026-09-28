export default function DebugTable({ rows }: { rows: Record<string, unknown>[] }) {
 if (!rows.length) return <p>No rows available.</p>;
 const keys=Array.from(new Set(rows.flatMap(Object.keys)));
 return <div className="table-scroll"><table><thead><tr>{keys.map(k=><th key={k}>{k.replaceAll('_',' ')}</th>)}</tr></thead><tbody>{rows.map((row,i)=><tr key={i}>{keys.map(k=><td key={k}>{typeof row[k]==='object'?JSON.stringify(row[k]):String(row[k]??'—')}</td>)}</tr>)}</tbody></table></div>;
}
