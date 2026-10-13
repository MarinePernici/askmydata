import hashlib
import secrets
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractBaseUser
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.authentication.exceptions import (
    AccountAlreadyExistsError,
    ActiveInvitationExistsError,
    InvalidAccessRequestError,
    InvalidInvitationError,
    InvitationExpiredError,
    PendingAccessRequestExistsError,
)
from apps.authentication.models import AccessRequest, Invitation


class InvitationService:
    DEFAULT_EXPIRATION_DAYS = 7

    def create(
        self,
        email: str,
        *,
        expiration_days: int = DEFAULT_EXPIRATION_DAYS,
        access_request: AccessRequest | None = None,
    ) -> tuple[Invitation, str]:
        normalized_email = email.strip().lower()
        User = get_user_model()

        if User.objects.filter(email__iexact=normalized_email).exists():
            raise AccountAlreadyExistsError("An account already exists for this email.")

        if Invitation.objects.filter(
            email__iexact=normalized_email,
            status=Invitation.Status.PENDING,
            expires_at__gt=timezone.now(),
        ).exists():
            raise ActiveInvitationExistsError(
                "An active invitation already exists for this email."
            )

        pending_requests = AccessRequest.objects.filter(
            email__iexact=normalized_email,
            status=AccessRequest.Status.PENDING,
        )

        if access_request is not None:
            pending_requests = pending_requests.exclude(pk=access_request.pk)

        if pending_requests.exists():
            raise PendingAccessRequestExistsError(
                "A pending access request already exists for this email."
            )

        raw_token = secrets.token_urlsafe(32)
        token_hash = self._hash_token(raw_token)

        invitation = Invitation.objects.create(
            email=normalized_email,
            token_hash=token_hash,
            expires_at=timezone.now() + timedelta(days=expiration_days),
        )

        return invitation, raw_token

    def get_by_token(self, raw_token: str) -> Invitation:
        token_hash = self._hash_token(raw_token)

        try:
            return Invitation.objects.get(token_hash=token_hash)
        except Invitation.DoesNotExist as exc:
            raise InvalidInvitationError("Invalid invitation.") from exc

    def validate(self, invitation: Invitation) -> None:
        if invitation.status != Invitation.Status.PENDING:
            raise InvalidInvitationError("Invitation is no longer valid.")

        if invitation.expires_at <= timezone.now():
            raise InvitationExpiredError("Invitation has expired.")

    def get_valid_by_token(self, raw_token: str) -> Invitation:
        invitation = self.get_by_token(raw_token)
        self.validate(invitation)

        return invitation

    def revoke(self, invitation: Invitation) -> None:
        if invitation.status != Invitation.Status.PENDING:
            raise InvalidInvitationError("Only pending invitations can be revoked.")

        invitation.status = Invitation.Status.REVOKED
        invitation.revoked_at = timezone.now()
        invitation.save(
            update_fields=[
                "status",
                "revoked_at",
            ]
        )

    def accept(
        self,
        raw_token: str,
        *,
        username: str,
        password: str,
    ) -> AbstractBaseUser:
        with transaction.atomic():
            token_hash = self._hash_token(raw_token)

            try:
                invitation = Invitation.objects.select_for_update().get(
                    token_hash=token_hash
                )
            except Invitation.DoesNotExist as exc:
                raise InvalidInvitationError("Invalid invitation.") from exc

            self.validate(invitation)

            user_model = get_user_model()
            user = user_model.objects.create_user(
                username=username,
                email=invitation.email,
                password=password,
            )

            invitation.status = Invitation.Status.ACCEPTED
            invitation.accepted_at = timezone.now()
            invitation.save(
                update_fields=[
                    "status",
                    "accepted_at",
                ]
            )

            return user

    @staticmethod
    def _hash_token(raw_token: str) -> str:
        return hashlib.sha256(raw_token.encode()).hexdigest()


class AccessRequestService:
    def create(
        self,
        *,
        first_name: str,
        last_name: str,
        email: str,
        reason: str,
    ) -> AccessRequest:
        normalized_email = email.strip().lower()
        User = get_user_model()

        if User.objects.filter(email__iexact=normalized_email).exists():
            raise AccountAlreadyExistsError("An account already exists for this email.")

        if Invitation.objects.filter(
            email__iexact=normalized_email,
            status=Invitation.Status.PENDING,
            expires_at__gt=timezone.now(),
        ).exists():
            raise ActiveInvitationExistsError(
                "An active invitation already exists for this email."
            )

        if AccessRequest.objects.filter(
            email__iexact=normalized_email,
            status=AccessRequest.Status.PENDING,
        ).exists():
            raise PendingAccessRequestExistsError(
                "A pending access request already exists for this email."
            )

        try:
            with transaction.atomic():
                return AccessRequest.objects.create(
                    first_name=first_name.strip(),
                    last_name=last_name.strip(),
                    email=normalized_email,
                    reason=reason.strip(),
                )
        except IntegrityError as exc:
            if AccessRequest.objects.filter(
                email__iexact=normalized_email,
                status=AccessRequest.Status.PENDING,
            ).exists():
                raise PendingAccessRequestExistsError(
                    "A pending access request already exists for this email."
                ) from exc

            raise

    def approve(
        self,
        access_request: AccessRequest,
    ) -> tuple[AccessRequest, Invitation, str]:
        with transaction.atomic():
            access_request = AccessRequest.objects.select_for_update().get(
                pk=access_request.pk
            )

            if access_request.status != AccessRequest.Status.PENDING:
                raise InvalidAccessRequestError(
                    "Only pending access requests can be approved."
                )

            invitation, raw_token = InvitationService().create(
                access_request.email,
                access_request=access_request,
            )

            access_request.status = AccessRequest.Status.APPROVED
            access_request.reviewed_at = timezone.now()
            access_request.invitation = invitation
            access_request.save(
                update_fields=[
                    "status",
                    "reviewed_at",
                    "invitation",
                ]
            )

        return access_request, invitation, raw_token

    def reject(self, access_request: AccessRequest) -> None:
        with transaction.atomic():
            access_request = AccessRequest.objects.select_for_update().get(
                pk=access_request.pk
            )

            if access_request.status != AccessRequest.Status.PENDING:
                raise InvalidAccessRequestError(
                    "Only pending access requests can be rejected."
                )

            access_request.status = AccessRequest.Status.REJECTED
            access_request.reviewed_at = timezone.now()
            access_request.save(
                update_fields=[
                    "status",
                    "reviewed_at",
                ]
            )
