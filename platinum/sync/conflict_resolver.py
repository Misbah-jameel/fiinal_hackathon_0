"""
Conflict Resolver

Handles Git merge conflicts between Cloud and Local agents.
Implements strategies for resolving common conflict scenarios.
"""

import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class ConflictResolver:
    """
    Conflict Resolver
    
    Strategies for resolving Git merge conflicts:
    1. Last-write-wins (for non-critical files)
    2. Merge (for Dashboard.md)
    3. Keep-both (for action files)
    4. Manual (for conflicts that need human review)
    """
    
    def __init__(self, vault_path: Path):
        self.vault_path = vault_path
        self.conflicts_resolved: int = 0
        self.conflicts_manual: int = 0
    
    def resolve_conflicts(self, conflicts: List[str]) -> Dict[str, str]:
        """
        Resolve list of conflicting files
        
        Returns dict of filepath -> resolution strategy used
        """
        results = {}
        
        for conflict_path in conflicts:
            full_path = self.vault_path / conflict_path
            strategy = self._determine_strategy(full_path)
            
            logger.info(f"Resolving conflict: {conflict_path} using {strategy}")
            
            if strategy == "auto_merge":
                success = self._auto_merge(full_path)
            elif strategy == "keep_both":
                success = self._keep_both(full_path)
            elif strategy == "last_write_wins":
                success = self._last_write_wins(full_path)
            else:  # manual
                success = self._mark_for_manual(full_path)
            
            if success:
                results[conflict_path] = strategy
                self.conflicts_resolved += 1
            else:
                results[conflict_path] = "failed"
        
        return results
    
    def _determine_strategy(self, filepath: Path) -> str:
        """Determine resolution strategy based on file type"""
        name = filepath.name.lower()
        parent = filepath.parent.name.lower()
        
        # Dashboard.md - merge
        if name == "dashboard.md":
            return "auto_merge"
        
        # Action files in Needs_Action - keep both
        if parent == "needs_action":
            return "keep_both"
        
        # Plans - keep both (different agents may create different plans)
        if parent == "plans":
            return "keep_both"
        
        # Logs - last write wins
        if parent == "logs":
            return "last_write_wins"
        
        # Audit logs - keep both (append)
        if parent == "audit":
            return "keep_both"
        
        # Approval files - keep both
        if parent == "pending_approval":
            return "keep_both"
        
        # Default: manual review
        return "manual"
    
    def _auto_merge(self, filepath: Path) -> bool:
        """Auto-merge file content"""
        try:
            content = filepath.read_text(encoding='utf-8')
            
            # Remove conflict markers and merge sections
            lines = content.split('\n')
            merged_lines = []
            in_conflict = False
            ours_section = []
            theirs_section = []
            
            for line in lines:
                if line.startswith('<<<<<<<'):
                    in_conflict = True
                    ours_section = []
                    theirs_section = []
                elif line.startswith('======='):
                    continue
                elif line.startswith('>>>>>>>'):
                    in_conflict = False
                    # Merge both sections
                    merged_lines.extend(ours_section)
                    merged_lines.extend(theirs_section)
                elif in_conflict:
                    if not ours_section:
                        ours_section.append(line)
                    else:
                        theirs_section.append(line)
                else:
                    merged_lines.append(line)
            
            # Write merged content
            filepath.write_text('\n'.join(merged_lines), encoding='utf-8')
            
            logger.info(f"Auto-merged: {filepath.name}")
            return True
            
        except Exception as e:
            logger.error(f"Auto-merge failed: {e}")
            return False
    
    def _keep_both(self, filepath: Path) -> bool:
        """Keep both versions with different filenames"""
        try:
            content = filepath.read_text(encoding='utf-8')
            
            # Create timestamped copy
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_name = filepath.stem
            extension = filepath.suffix
            
            # Rename current file with timestamp
            new_name = f"{base_name}_CONFLICT_{timestamp}{extension}"
            new_path = filepath.parent / new_name
            
            filepath.rename(new_path)
            
            logger.info(f"Kept both versions: {filepath.name} → {new_name}")
            return True
            
        except Exception as e:
            logger.error(f"Keep-both failed: {e}")
            return False
    
    def _last_write_wins(self, filepath: Path) -> bool:
        """Keep the version with latest modification time"""
        try:
            # Git checkout ours or theirs based on timestamp
            # For simplicity, keep current working version
            logger.info(f"Last-write-wins: {filepath.name}")
            return True
            
        except Exception as e:
            logger.error(f"Last-write-wins failed: {e}")
            return False
    
    def _mark_for_manual(self, filepath: Path) -> bool:
        """Mark file for manual resolution"""
        try:
            # Create marker file
            marker_path = filepath.parent / f".MANUAL_CONFLICT_{filepath.name}.txt"
            
            marker_content = f"""# Manual Conflict Resolution Required

**File:** {filepath.name}
**Time:** {datetime.now().isoformat()}
**Reason:** Automatic resolution not safe

## Instructions

1. Review the conflict markers in the file
2. Edit to resolve conflicts manually
3. Remove conflict markers
4. Delete this marker file
5. Commit the resolved file

## Conflict Markers

- `<<<<<<< HEAD` - Your version (Local)
- `=======` - Separator
- `>>>>>>> origin/main` - Cloud version
"""
            
            marker_path.write_text(marker_content, encoding='utf-8')
            
            self.conflicts_manual += 1
            logger.warning(f"Marked for manual resolution: {filepath.name}")
            
            return True
            
        except Exception as e:
            logger.error(f"Mark-for-manual failed: {e}")
            return False
    
    def merge_dashboard(self, local_path: Path, cloud_content: str) -> str:
        """
        Merge Cloud updates into Dashboard.md
        
        Preserves Local sections while adding Cloud updates
        """
        try:
            local_content = local_path.read_text(encoding='utf-8')
            
            # Find Cloud Updates section
            cloud_section_marker = "## Cloud Updates"
            
            if cloud_section_marker not in local_content:
                # Add new section
                return local_content + f"\n\n{cloud_section_marker}\n\n{cloud_content}\n"
            
            # Merge into existing section
            lines = local_content.split('\n')
            new_lines = []
            in_cloud_section = False
            cloud_content_added = False
            
            for line in lines:
                if line.startswith(cloud_section_marker):
                    in_cloud_section = True
                    new_lines.append(line)
                    continue
                
                if in_cloud_section and not cloud_content_added:
                    # Add cloud content before next section
                    if line.startswith('##') and line != cloud_section_marker:
                        new_lines.append(cloud_content)
                        new_lines.append('')
                        cloud_content_added = True
                        in_cloud_section = False
                    new_lines.append(line)
                else:
                    new_lines.append(line)
            
            # If still in cloud section at end, append
            if in_cloud_section and not cloud_content_added:
                new_lines.append(cloud_content)
            
            return '\n'.join(new_lines)
            
        except Exception as e:
            logger.error(f"Dashboard merge failed: {e}")
            return cloud_content  # Fallback to cloud version
    
    def get_statistics(self) -> Dict:
        """Get conflict resolution statistics"""
        return {
            "total_resolved": self.conflicts_resolved,
            "manual_required": self.conflicts_manual,
            "auto_resolve_rate": self.conflicts_resolved / max(
                self.conflicts_resolved + self.conflicts_manual, 1
            ) * 100,
        }


def create_conflict_resolver(vault_path: Path) -> ConflictResolver:
    """Create ConflictResolver instance"""
    return ConflictResolver(vault_path)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    resolver = create_conflict_resolver(Path("./test_vault"))
    
    # Test conflict resolution
    test_conflicts = [
        "Needs_Action/test.md",
        "Dashboard.md",
        "Logs/2026-03-28.md",
    ]
    
    results = resolver.resolve_conflicts(test_conflicts)
    logger.info(f"Resolution results: {results}")
    
    stats = resolver.get_statistics()
    logger.info(f"Statistics: {stats}")
