import { MARK_TO_IMAGE } from '../logic/constants';
import type { Mark } from '../logic/constants';
import './tile.css';

type Props = {
  mark: Mark;
  selected: boolean;
  onToggle: () => void;
  sizePx: number;
};

export function Tile({ mark, selected, onToggle, sizePx }: Props) {
  return (
    <button
      className={`tile ${selected ? 'selected' : ''}`}
      onClick={onToggle}
      style={{ width: sizePx, height: sizePx }}
      aria-pressed={selected}
    >
      <img src={MARK_TO_IMAGE[mark]} alt={mark} draggable={false} />
      <span className="overlay" />
    </button>
  );
}

export default Tile;

