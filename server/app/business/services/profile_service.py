"""Profile management service."""

import re
from typing import List, Dict, Any, Optional
from app.data.oracle.profile_dao import profile_dao


class ProfileService:
    """Service for profile management operations."""

    def _validate_profile_name(self, profile_name: str) -> bool:
        """Validate profile name format (alphanumeric and underscore only)."""
        return bool(re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', profile_name))

    def _validate_resource_limit(self, value: str) -> bool:
        """
        Validate resource limit value.
        Valid values: UNLIMITED, DEFAULT, or a positive integer.
        """
        if value.upper() in ("UNLIMITED", "DEFAULT"):
            return True
        try:
            int_val = int(value)
            return int_val > 0
        except ValueError:
            return False

    def _normalize_resource_limit(self, value: str) -> str:
        """Normalize resource limit value to uppercase or integer string."""
        upper_val = value.upper().strip()
        if upper_val in ("UNLIMITED", "DEFAULT"):
            return upper_val
        return value.strip()

    async def get_all_profiles(self) -> List[Dict[str, Any]]:
        """Get all profiles from DBA_PROFILES."""
        return await profile_dao.query_all_profiles()

    async def get_profile_detail(self, profile_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information for a specific profile."""
        return await profile_dao.get_profile_detail(profile_name)

    async def create_profile(
        self,
        profile_name: str,
        sessions_per_user: str = "DEFAULT",
        connect_time: str = "DEFAULT",
        idle_time: str = "DEFAULT",
    ) -> None:
        """
        Create a new profile with validation.
        
        Args:
            profile_name: Profile name
            sessions_per_user: SESSIONS_PER_USER limit
            connect_time: CONNECT_TIME limit
            idle_time: IDLE_TIME limit
            
        Raises:
            ValueError: If validation fails
        """
        # Validate profile name
        if not self._validate_profile_name(profile_name):
            raise ValueError(
                "Invalid profile name. Must start with a letter and contain only "
                "alphanumeric characters and underscores."
            )
        
        # Check reserved names
        if profile_name.upper() == "DEFAULT":
            raise ValueError("Cannot create profile with name 'DEFAULT'. It is a reserved name.")
        
        # Check if profile already exists
        if await profile_dao.profile_exists(profile_name):
            raise ValueError(f"Profile '{profile_name}' already exists.")
        
        # Validate resource limits
        for name, value in [
            ("SESSIONS_PER_USER", sessions_per_user),
            ("CONNECT_TIME", connect_time),
            ("IDLE_TIME", idle_time),
        ]:
            if not self._validate_resource_limit(value):
                raise ValueError(
                    f"Invalid {name} value: '{value}'. "
                    "Must be UNLIMITED, DEFAULT, or a positive integer."
                )
        
        # Normalize and create
        await profile_dao.create_profile_ddl(
            profile_name=profile_name,
            sessions_per_user=self._normalize_resource_limit(sessions_per_user),
            connect_time=self._normalize_resource_limit(connect_time),
            idle_time=self._normalize_resource_limit(idle_time),
        )

    async def update_profile(
        self,
        profile_name: str,
        sessions_per_user: Optional[str] = None,
        connect_time: Optional[str] = None,
        idle_time: Optional[str] = None,
    ) -> None:
        """
        Update profile resource limits.
        
        Args:
            profile_name: Profile name
            sessions_per_user: New SESSIONS_PER_USER limit (optional)
            connect_time: New CONNECT_TIME limit (optional)
            idle_time: New IDLE_TIME limit (optional)
            
        Raises:
            ValueError: If validation fails
        """
        # Check if profile exists
        if not await profile_dao.profile_exists(profile_name):
            raise ValueError(f"Profile '{profile_name}' does not exist.")
        
        # Validate provided resource limits
        normalized_values = {}
        
        if sessions_per_user is not None:
            if not self._validate_resource_limit(sessions_per_user):
                raise ValueError(
                    f"Invalid SESSIONS_PER_USER value: '{sessions_per_user}'. "
                    "Must be UNLIMITED, DEFAULT, or a positive integer."
                )
            normalized_values["sessions_per_user"] = self._normalize_resource_limit(sessions_per_user)
        
        if connect_time is not None:
            if not self._validate_resource_limit(connect_time):
                raise ValueError(
                    f"Invalid CONNECT_TIME value: '{connect_time}'. "
                    "Must be UNLIMITED, DEFAULT, or a positive integer."
                )
            normalized_values["connect_time"] = self._normalize_resource_limit(connect_time)
        
        if idle_time is not None:
            if not self._validate_resource_limit(idle_time):
                raise ValueError(
                    f"Invalid IDLE_TIME value: '{idle_time}'. "
                    "Must be UNLIMITED, DEFAULT, or a positive integer."
                )
            normalized_values["idle_time"] = self._normalize_resource_limit(idle_time)
        
        if not normalized_values:
            return  # Nothing to update
        
        await profile_dao.alter_profile_ddl(profile_name, **normalized_values)

    async def delete_profile(self, profile_name: str, cascade: bool = False) -> None:
        """
        Delete a profile.
        
        Args:
            profile_name: Profile name
            cascade: Whether to reassign users to DEFAULT profile
            
        Raises:
            ValueError: If validation fails
        """
        # Check reserved profiles
        if profile_name.upper() == "DEFAULT":
            raise ValueError("Cannot delete the DEFAULT profile.")
        
        # Check if profile exists
        if not await profile_dao.profile_exists(profile_name):
            raise ValueError(f"Profile '{profile_name}' does not exist.")
        
        # Check for users if not cascading
        if not cascade:
            users = await profile_dao.query_profile_users(profile_name)
            if users:
                raise ValueError(
                    f"Profile '{profile_name}' is assigned to {len(users)} user(s). "
                    "Use cascade option to reassign them to DEFAULT profile."
                )
        
        await profile_dao.drop_profile_ddl(profile_name, cascade=cascade)

    async def get_profile_users(self, profile_name: str) -> List[Dict[str, Any]]:
        """Get list of users assigned to a profile."""
        return await profile_dao.query_profile_users(profile_name)


# Global service instance
profile_service = ProfileService()
